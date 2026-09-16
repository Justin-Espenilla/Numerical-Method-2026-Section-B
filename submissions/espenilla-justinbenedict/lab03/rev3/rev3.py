"""
rev3.py - Revit 3 Solver Update (Architecture-First)
6m Cube with Unit-System, Material Library (ASTM A36), and Section Assignment.

Architecture: Model -> UnitSystem + MaterialLibrary + SectionLibrary + Members
Members: Column (M9-M12), Roof Beam (M5-M8), Tie Beam (M1-M4) each with material+section refs.
Units: centralized conversions from units.zip Units/Units_Imperial_Metric.xlsx
       Base definitions (NIST SP 811): 1 in=25.4 mm, 1 lbf=4.4482216152605 N, g=9.80665 m/s2
       Derived factors formulas D12:D30 -> no scattered factors.
Materials: member property, not global. A36 via library.
Sections:  member property, per-member distinct sizing.

Usage:
    python rev3.py                         # demo Imperial + Metric cube, validates
    python rev3.py --excel --plot          # single Excel + single Figure (METRIC default, headless best)
    python rev3.py --excel --plot --imperial  # same but IMPERIAL ft
    python rev3.py --excel --plot --show   # also pop figure window
    from rev3 import create_revit3_cube, UnitSystem, MemberType
    m = create_revit3_cube(unit_system=UnitSystem.METRIC, sections={...})
"""
from __future__ import annotations
import math
import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 1. UNIT SYSTEM  (authoritative: units.zip / Units_Imperial_Metric.xlsx)
# ---------------------------------------------------------------------------

class UnitSystem(str, enum.Enum):
    IMPERIAL = "IMPERIAL"   # ft, in, kip, ksi, pcf, 1e-5/F
    METRIC = "METRIC"       # m, mm, kN, MPa, kN/m3, 1e-6/C  (Standard Metric / SI)

# Base definitions (exact, NIST SP 811) - Units.xlsx B4:B8
BASE = {
    "inch_to_mm": 25.4,                      # B4  1 in = 25.4 mm
    "lbf_to_N": 4.4482216152605,              # B5  1 lbf = 4.448... N
    "g_m_s2": 9.80665,                        # B6  standard gravity
    "kip_to_lbf": 1000.0,                     # B7  1 kip = 1000 lbf
    "ft_to_in": 12.0,                         # B8  1 ft = 12 in
}

# Derived conversion factors (multiply Imperial by => Metric)  - Units.xlsx D12:D30
# Formulas preserved; values are BASE-derived, not hardcoded magic.
_derived = {}
_derived["in_to_mm"] = BASE["inch_to_mm"]                                          # D12 =B4
_derived["ft_to_m"] = BASE["inch_to_mm"] * BASE["ft_to_in"] / 1000.0               # D13 =B4*B8/1000
_derived["in2_to_mm2"] = BASE["inch_to_mm"] ** 2                                   # D14 =B4^2
_derived["in4_to_mm4"] = BASE["inch_to_mm"] ** 4                                   # D15 =B4^4
_derived["in3_to_mm3"] = BASE["inch_to_mm"] ** 3                                   # D16 =B4^3
_derived["kip_to_kN"] = BASE["lbf_to_N"] * BASE["kip_to_lbf"] / 1000.0              # D17 =B5*B7/1000
_derived["lbf_to_N"] = BASE["lbf_to_N"]                                            # D18 =B5
_derived["kip_ft_to_kN_m"] = BASE["lbf_to_N"] * BASE["kip_to_lbf"] / 1000.0 * BASE["inch_to_mm"] * BASE["ft_to_in"] / 1000.0  # D19 kN*m
_derived["kip_in_to_kN_m"] = BASE["lbf_to_N"] * BASE["kip_to_lbf"] / 1000.0 * BASE["inch_to_mm"] / 1000.0  # D20
_derived["ksi_to_MPa"] = BASE["lbf_to_N"] * BASE["kip_to_lbf"] / (BASE["inch_to_mm"] ** 2)  # D21  kN/mm2*1000
_derived["psi_to_kPa"] = BASE["lbf_to_N"] / (BASE["inch_to_mm"] ** 2) * 1000.0     # D22
_derived["ksi_to_GPa"] = _derived["ksi_to_MPa"] / 1000.0                           # D23
_derived["kip_per_ft_to_kN_per_m"] = _derived["kip_to_kN"] / _derived["ft_to_m"]  # D24
_derived["psf_to_kPa"] = BASE["lbf_to_N"] / ((BASE["inch_to_mm"] * BASE["ft_to_in"] / 1000.0) ** 2) / 1000.0  # D25
_derived["k_per_ft3_to_kN_per_m3"] = BASE["lbf_to_N"] * BASE["kip_to_lbf"] / 1000.0 / ((BASE["inch_to_mm"] * BASE["ft_to_in"] / 1000.0) ** 3)  # D26
_derived["pcf_to_kN_per_m3"] = BASE["lbf_to_N"] / ((BASE["inch_to_mm"] * BASE["ft_to_in"] / 1000.0) ** 3) / 1000.0  # D27
_derived["thermal_1e5_per_F_to_1e6_per_C"] = 1.8 * 10.0                             # D29
_derived["per_F_to_per_C"] = 1.8                                                   # D30

# Expose as CONVERSIONS (Imperial -> Metric)
CONVERSIONS: Dict[str, float] = dict(_derived)

# Reverse (Metric -> Imperial) = 1 / Imperial->Metric
CONVERSIONS_REVERSE: Dict[str, float] = {k: 1.0 / v for k, v in CONVERSIONS.items() if v != 0}

# Quantity -> (imperial unit, metric unit, imperial_to_metric factor key)
QUANTITY_DEF = {
    "length_ft_m": ("ft", "m", "ft_to_m"),
    "length_in_mm": ("in", "mm", "in_to_mm"),
    "area": ("in2", "mm2", "in2_to_mm2"),
    "moment_of_inertia": ("in4", "mm4", "in4_to_mm4"),
    "section_modulus": ("in3", "mm3", "in3_to_mm3"),
    "force_kip_kN": ("kip", "kN", "kip_to_kN"),
    "moment_kip_ft": ("kip-ft", "kN-m", "kip_ft_to_kN_m"),
    "moment_kip_in": ("kip-in", "kN-m", "kip_in_to_kN_m"),
    "stress_ksi_MPa": ("ksi", "MPa", "ksi_to_MPa"),
    "stress_ksi_GPa": ("ksi", "GPa", "ksi_to_GPa"),
    "distributed_load": ("kip/ft", "kN/m", "kip_per_ft_to_kN_per_m"),
    "area_load": ("psf", "kPa", "psf_to_kPa"),
    "unit_weight_kft3": ("k/ft3", "kN/m3", "k_per_ft3_to_kN_per_m3"),
    "unit_weight_pcf": ("pcf", "kN/m3", "pcf_to_kN_per_m3"),
}

# Solver internal: single consistent length = meter (m), force = kilonewton (kN)
# So all internal values are in m / kN / kN-m / kPa (kN/m2) with MPa as presentation.
# This avoids RISA's ft+in mix (see Unit Systems sheet note).
SOLVER_INTERNAL = {
    "length": "m",
    "force": "kN",
    "stress": "kPa",  # kN/m2; MPa = kPa/1000 for presentation
    "moment": "kN-m",
    "distributed_load": "kN/m",
    "area_load": "kPa",
}


def convert(value: float, quantity_key: str, from_system: UnitSystem, to_system: UnitSystem) -> float:
    """Centralized conversion. No scattered factors elsewhere."""
    if from_system == to_system:
        return float(value)
    if quantity_key not in QUANTITY_DEF:
        raise ValueError(f"Unknown quantity '{quantity_key}'. Valid: {list(QUANTITY_DEF)}")
    _, _, factor_key = QUANTITY_DEF[quantity_key]
    factor = CONVERSIONS[factor_key]  # Imperial -> Metric
    if from_system == UnitSystem.IMPERIAL and to_system == UnitSystem.METRIC:
        return float(value) * factor
    elif from_system == UnitSystem.METRIC and to_system == UnitSystem.IMPERIAL:
        return float(value) / factor
    else:
        raise ValueError(f"Unsupported system pair {from_system}->{to_system}")


def convert_temperature(value: float, from_system: UnitSystem, to_system: UnitSystem) -> float:
    """Temperature offset conversion: C = (F-32)/1.8. Not a factor."""
    if from_system == to_system:
        return float(value)
    if from_system == UnitSystem.IMPERIAL and to_system == UnitSystem.METRIC:
        return (float(value) - 32.0) / 1.8
    else:
        return float(value) * 1.8 + 32.0


def validate_unit_system(name: str) -> UnitSystem:
    try:
        return UnitSystem(name)
    except ValueError:
        raise ValueError(f"Invalid unit system '{name}'. Valid: {[e.value for e in UnitSystem]}")


# ---------------------------------------------------------------------------
# 2. MATERIAL LIBRARY  (A36 Steel - AISC 360-16)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Material:
    name: str
    # Mechanical - stored in solver internal (kPa, but expose MPa/ksi helpers)
    E_kPa: float        # Young's modulus  kPa  (internal F/L2)
    G_kPa: float        # Shear modulus
    nu: float           # Poisson
    Fy_kPa: float       # Yield
    Fu_kPa: float       # Ultimate
    alpha_per_C: float  # thermal coeff /C
    density_kg_m3: float
    weight_kN_m3: float
    # Presentation helpers
    @property
    def E_MPa(self) -> float: return self.E_kPa / 1000.0
    @property
    def E_ksi(self) -> float: return self.E_kPa / CONVERSIONS["ksi_to_MPa"] / 1000.0  # kPa->MPa->ksi
    @property
    def E_GPa(self) -> float: return self.E_kPa / 1e6
    @property
    def Fy_MPa(self) -> float: return self.Fy_kPa / 1000.0
    @property
    def Fy_ksi(self) -> float: return self.Fy_kPa / CONVERSIONS["ksi_to_MPa"] / 1000.0
    @property
    def G_MPa(self) -> float: return self.G_kPa / 1000.0
    @property
    def alpha_per_F(self) -> float: return self.alpha_per_C / CONVERSIONS["per_F_to_per_C"]
    @property
    def weight_pcf(self) -> float: return self.weight_kN_m3 / CONVERSIONS["pcf_to_kN_per_m3"]
    @property
    def weight_k_per_ft3(self) -> float: return self.weight_kN_m3 / CONVERSIONS["k_per_ft3_to_kN_per_m3"]


class UnknownMaterialError(KeyError):
    pass


class MaterialLibrary:
    def __init__(self):
        self._mats: Dict[str, Material] = {}

    def add(self, mat: Material):
        if mat.name in self._mats:
            raise ValueError(f"Material '{mat.name}' already exists")
        self._mats[mat.name] = mat

    def get(self, name: str) -> Material:
        if name not in self._mats:
            raise UnknownMaterialError(f"Material '{name}' not in library. Available: {list(self._mats)}")
        return self._mats[name]

    def __contains__(self, name: str) -> bool:
        return name in self._mats

    def names(self) -> List[str]:
        return list(self._mats.keys())

    def __len__(self):
        return len(self._mats)


def default_material_library() -> MaterialLibrary:
    lib = MaterialLibrary()
    # ASTM A36 - AISC 360-16: E=29000 ksi (200 GPa), G=11200 ksi (77.2 GPa), nu=0.30,
    # Fy=36 ksi (250 MPa), Fu=58 ksi (400 MPa), alpha=6.5e-6 /F (11.7e-6 /C), weight 490 pcf (77 kN/m3), density 7850 kg/m3
    # Stored internal kPa for solver consistency.
    E_MPa = 200000.0  # spec Converter shows 29000 ksi ->199948 MPa; use 200 GPa canonical
    E_kPa = E_MPa * 1000.0
    G_MPa = 77200.0
    G_kPa = G_MPa * 1000.0
    Fy_MPa = 250.0
    Fu_MPa = 400.0
    lib.add(Material(
        name="ASTM A36",
        E_kPa=E_kPa, G_kPa=G_kPa, nu=0.30,
        Fy_kPa=Fy_MPa * 1000.0, Fu_kPa=Fu_MPa * 1000.0,
        alpha_per_C=11.7e-6,
        density_kg_m3=7850.0,
        weight_kN_m3=77.0,  # ~76.97 from Converter for 0.49 k/ft3
    ))
    # Alias without space for convenience
    lib.add(Material(
        name="A36",
        E_kPa=E_kPa, G_kPa=G_kPa, nu=0.30,
        Fy_kPa=Fy_MPa * 1000.0, Fu_kPa=Fu_MPa * 1000.0,
        alpha_per_C=11.7e-6,
        density_kg_m3=7850.0,
        weight_kN_m3=77.0,
    ))
    return lib


# ---------------------------------------------------------------------------
# 3. SECTION / MEMBER-SIZE LIBRARY
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Section:
    name: str
    # Stored internal m2 / m4 / m3
    A_m2: float
    Iy_m4: float
    Iz_m4: float
    J_m4: float = 0.0
    Sy_m3: float = 0.0
    Sz_m3: float = 0.0
    # optional dims for reporting
    d_m: float = 0.0
    bf_m: float = 0.0
    # imperial helpers
    @property
    def A_in2(self) -> float: return self.A_m2 / (CONVERSIONS["ft_to_m"]**2) * (12.0**2)  # m2->in2 via ft->m then 144 in2/ft2
    # Simpler: use in2_to_mm2 -> m2 = mm2 *1e-6, so in2 = mm2 *0.00155, mm2 = m2*1e6
    def _A_mm2(self) -> float: return self.A_m2 * 1e6
    @property
    def A_mm2(self) -> float: return self.A_m2 * 1e6
    @property
    def display_A(self) -> Tuple[float, str]:
        return (self.A_mm2, "mm2")


class UnknownSectionError(KeyError):
    pass


class SectionLibrary:
    def __init__(self):
        self._secs: Dict[str, Section] = {}

    def add(self, sec: Section):
        if sec.name in self._secs:
            raise ValueError(f"Section '{sec.name}' already exists")
        self._secs[sec.name] = sec

    def get(self, name: str) -> Section:
        if name not in self._secs:
            raise UnknownSectionError(f"Section '{name}' not in library. Available: {list(self._secs)}")
        return self._secs[name]

    def __contains__(self, name: str) -> bool:
        return name in self._secs

    def names(self) -> List[str]:
        return list(self._secs.keys())

    def __len__(self):
        return len(self._secs)


def _in2_to_m2(in2: float) -> float:
    return in2 * CONVERSIONS["in2_to_mm2"] * 1e-6  # in2->mm2 * mm2->m2

def _in4_to_m4(in4: float) -> float:
    return in4 * CONVERSIONS["in4_to_mm4"] * 1e-12  # mm4->m4

def _in3_to_m3(in3: float) -> float:
    return in3 * CONVERSIONS["in3_to_mm3"] * 1e-9


def default_section_library() -> SectionLibrary:
    lib = SectionLibrary()
    # Stubs from Converter example: W12x26 A=7.65 in2, Iz=204 in4 ; add two more for distinct sizing
    # W12x26 -> Column
    lib.add(Section(name="W12x26", A_m2=_in2_to_m2(7.65), Iy_m4=_in4_to_m4(204*0.4), Iz_m4=_in4_to_m4(204), J_m4=_in4_to_m4(0.30), Sy_m3=_in3_to_m3(38.4), Sz_m3=_in3_to_m3(33.4), d_m=0.310, bf_m=0.165))
    # W10x22 -> Roof Beam
    lib.add(Section(name="W10x22", A_m2=_in2_to_m2(6.49), Iy_m4=_in4_to_m4(118*0.35), Iz_m4=_in4_to_m4(118), J_m4=_in4_to_m4(0.21), Sy_m3=_in3_to_m3(23.2), Sz_m3=_in3_to_m3(19.8), d_m=0.262, bf_m=0.146))
    # W8x18 -> Tie Beam
    lib.add(Section(name="W8x18", A_m2=_in2_to_m2(5.26), Iy_m4=_in4_to_m4(61.9*0.32), Iz_m4=_in4_to_m4(61.9), J_m4=_in4_to_m4(0.15), Sy_m3=_in3_to_m3(15.3), Sz_m3=_in3_to_m3(12.1), d_m=0.206, bf_m=0.133))
    # Also add metric-named aliases for SI presentation
    lib.add(Section(name="W310x39", A_m2=_in2_to_m2(7.65), Iy_m4=_in4_to_m4(204*0.4), Iz_m4=_in4_to_m4(204), J_m4=_in4_to_m4(0.30), Sy_m3=_in3_to_m3(38.4), Sz_m3=_in3_to_m3(33.4), d_m=0.310, bf_m=0.165))
    return lib


# ---------------------------------------------------------------------------
# 4. STRUCTURAL MODEL (Revit 3 Cube)
# ---------------------------------------------------------------------------

class MemberType(str, enum.Enum):
    COLUMN = "COLUMN"       # M9-M12 vertical
    ROOF_BEAM = "ROOF_BEAM" # M5-M8 top
    TIE_BEAM = "TIE_BEAM"   # M1-M4 bottom


@dataclass
class Member:
    id: str
    i: int
    j: int
    member_type: MemberType
    material: str = "ASTM A36"
    section: str = "W12x26"
    beta_deg: float = 0.0
    releases: Dict = field(default_factory=lambda: {"start": {"Fx": 0, "Mz": 0}, "end": {"Fx": 0, "Mz": 0}})

    def validate(self, mat_lib: MaterialLibrary, sec_lib: SectionLibrary):
        if self.material not in mat_lib:
            raise UnknownMaterialError(f"Member {self.id} material '{self.material}' not found in library {mat_lib.names()}")
        if self.section not in sec_lib:
            raise UnknownSectionError(f"Member {self.id} section '{self.section}' not found in library {sec_lib.names()}")
        if not isinstance(self.member_type, MemberType):
            raise ValueError(f"Member {self.id} invalid member_type {self.member_type}")


@dataclass
class Revit3Model:
    unit_system: UnitSystem
    nodes: Dict[int, Tuple[float, float, float]]  # internal m
    members: List[Member]
    supports: Dict[int, Dict]
    material_library: MaterialLibrary
    section_library: SectionLibrary
    size_m: float = 6.0  # internal
    name: str = "Revit 3 Cube 6m"

    def validate(self):
        validate_unit_system(self.unit_system.value)
        if len(self.nodes) != 8:
            raise ValueError(f"Revit3 cube requires 8 nodes, got {len(self.nodes)}")
        if len(self.members) != 12:
            raise ValueError(f"Revit3 cube requires 12 members, got {len(self.members)}")
        for m in self.members:
            m.validate(self.material_library, self.section_library)
        # check all member node refs exist
        for m in self.members:
            if m.i not in self.nodes or m.j not in self.nodes:
                raise ValueError(f"Member {m.id} references missing node {m.i}->{m.j}")
        return True

    def get_material(self, member: Member) -> Material:
        return self.material_library.get(member.material)

    def get_section(self, member: Member) -> Section:
        return self.section_library.get(member.section)

    def summary(self) -> str:
        lines = [f"{self.name} | UnitSystem={self.unit_system.value} | size={self.size_m:.2f} m internal ({self.size_m / CONVERSIONS['ft_to_m']:.2f} ft Imperial) | Members={len(self.members)}"]
        lines.append(f"  Material library: {self.material_library.names()}")
        lines.append(f"  Section library: {self.section_library.names()}")
        for m in self.members:
            mat = self.get_material(m)
            sec = self.get_section(m)
            lines.append(f"  {m.id:3s} {m.member_type.value:9s} {m.i}->{m.j}  mat={m.material} (E={mat.E_MPa:.0f} MPa/{mat.E_ksi:.0f} ksi)  sec={m.section} (A={sec.A_mm2:.0f} mm2)")
        return "\n".join(lines)


# Default cube topology (same as python-2/cube.py:30-54)
_DEFAULT_NODES_M = {
    1: (0.0, 0.0, 0.0),
    2: (6.0, 0.0, 0.0),
    3: (6.0, 0.0, 6.0),
    4: (0.0, 0.0, 6.0),
    5: (0.0, 6.0, 0.0),
    6: (6.0, 6.0, 0.0),
    7: (6.0, 6.0, 6.0),
    8: (0.0, 6.0, 6.0),
}
_DEFAULT_MEMBERS_RAW = [
    ("M1", 1, 2, MemberType.TIE_BEAM),
    ("M2", 2, 3, MemberType.TIE_BEAM),
    ("M3", 3, 4, MemberType.TIE_BEAM),
    ("M4", 4, 1, MemberType.TIE_BEAM),
    ("M5", 5, 6, MemberType.ROOF_BEAM),
    ("M6", 6, 7, MemberType.ROOF_BEAM),
    ("M7", 7, 8, MemberType.ROOF_BEAM),
    ("M8", 8, 5, MemberType.ROOF_BEAM),
    ("M9", 1, 5, MemberType.COLUMN),
    ("M10", 2, 6, MemberType.COLUMN),
    ("M11", 3, 7, MemberType.COLUMN),
    ("M12", 4, 8, MemberType.COLUMN),
]
_DEFAULT_SUPPORTS = {
    1: {"type": "PINNED", "Tx": 0, "Ty": 0, "Tz": 0, "Rx": 1, "Ry": 1, "Rz": 1},
    2: {"type": "PINNED", "Tx": 0, "Ty": 0, "Tz": 0, "Rx": 1, "Ry": 1, "Rz": 1},
    3: {"type": "PINNED", "Tx": 0, "Ty": 0, "Tz": 0, "Rx": 1, "Ry": 1, "Rz": 1},
    4: {"type": "PINNED", "Tx": 0, "Ty": 0, "Tz": 0, "Rx": 1, "Ry": 1, "Rz": 1},
    5: {"type": "FREE", "Tx": 1, "Ty": 1, "Tz": 1, "Rx": 1, "Ry": 1, "Rz": 1},
    6: {"type": "FREE", "Tx": 1, "Ty": 1, "Tz": 1, "Rx": 1, "Ry": 1, "Rz": 1},
    7: {"type": "FREE", "Tx": 1, "Ty": 1, "Tz": 1, "Rx": 1, "Ry": 1, "Rz": 1},
    8: {"type": "FREE", "Tx": 1, "Ty": 1, "Tz": 1, "Rx": 1, "Ry": 1, "Rz": 1},
}


def create_revit3_cube(
    unit_system: UnitSystem = UnitSystem.METRIC,
    size: float = 6.0,  # in unit_system's length unit (ft if Imperial, m if Metric)
    material: str = "ASTM A36",
    sections: Optional[Dict[MemberType, str]] = None,
    member_materials: Optional[Dict[str, str]] = None,
    member_sections: Optional[Dict[str, str]] = None,
    material_library: Optional[MaterialLibrary] = None,
    section_library: Optional[SectionLibrary] = None,
) -> Revit3Model:
    """
    Create Revit 3 cube model.
    - size is interpreted in unit_system units, stored internal m.
    - sections: per-type default {COLUMN:W12x26, ROOF_BEAM:W10x22, TIE_BEAM:W8x18}
    - member_materials/member_sections: per-member override {mid: name}
    """
    if isinstance(unit_system, str):
        unit_system = validate_unit_system(unit_system)
    mat_lib = material_library or default_material_library()
    sec_lib = section_library or default_section_library()

    if material not in mat_lib:
        raise UnknownMaterialError(f"Default material '{material}' not in library")

    # default per-type sections (distinct, proves not global)
    if sections is None:
        sections = {
            MemberType.COLUMN: "W12x26",
            MemberType.ROOF_BEAM: "W10x22",
            MemberType.TIE_BEAM: "W8x18",
        }
    for t, sec_name in sections.items():
        if sec_name not in sec_lib:
            raise UnknownSectionError(f"Default section for {t} '{sec_name}' not in library")

    # size -> internal m
    size_m = float(size)
    if unit_system == UnitSystem.IMPERIAL:
        size_m = convert(size_m, "length_ft_m", UnitSystem.IMPERIAL, UnitSystem.METRIC)

    # nodes internal m (scale)
    scale = size_m / 6.0
    nodes_m = {nid: (x * scale, y * scale, z * scale) for nid, (x, y, z) in _DEFAULT_NODES_M.items()}

    members: List[Member] = []
    for mid, i, j, mtype in _DEFAULT_MEMBERS_RAW:
        mat = (member_materials or {}).get(mid, material if sections.get(mtype) else material)
        # but allow per-type material future: currently all A36
        if mid in (member_materials or {}):
            mat = member_materials[mid]
        sec = (member_sections or {}).get(mid, sections[mtype])
        # bottom beams pinned Mz per cube.py:85-89
        if mtype == MemberType.TIE_BEAM:
            releases = {"start": {"Fx": 0, "Mz": 1}, "end": {"Fx": 0, "Mz": 1}}
        else:
            releases = {"start": {"Fx": 0, "Mz": 0}, "end": {"Fx": 0, "Mz": 0}}
        m = Member(id=mid, i=i, j=j, member_type=mtype, material=mat, section=sec, beta_deg=0.0, releases=releases)
        members.append(m)

    model = Revit3Model(
        unit_system=unit_system,
        nodes=nodes_m,
        members=members,
        supports=dict(_DEFAULT_SUPPORTS),
        material_library=mat_lib,
        section_library=sec_lib,
        size_m=size_m,
    )
    model.validate()
    return model


def member_length_m(model: Revit3Model, member: Member) -> float:
    x1, y1, z1 = model.nodes[member.i]
    x2, y2, z2 = model.nodes[member.j]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


# ---------------------------------------------------------------------------
# 5. EXCEL / PLOT helpers (update to include new columns)
# ---------------------------------------------------------------------------

def create_excel(model: Revit3Model, filepath: str = "rev3_demo.xlsx"):
    """Create workbook mirroring cube.py but with Material/Section/Unit columns."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise ImportError("openpyxl required: pip install openpyxl")
    import os
    if not os.path.isabs(filepath):
        filepath = os.path.join(os.path.dirname(__file__), filepath)
    wb = Workbook()
    header_font = Font(bold=True, color="FFFFFF", size=10)
    header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin = Border(left=Side("thin", "B0B0B0"), right=Side("thin", "B0B0B0"), top=Side("thin", "B0B0B0"), bottom=Side("thin", "B0B0B0"))
    # Units for headers
    len_unit = "m" if model.unit_system == UnitSystem.METRIC else "ft"
    sec_len_unit = "mm" if model.unit_system == UnitSystem.METRIC else "in"

    # Sheet 1: Nodes (show both internal m and display)
    ws = wb.active
    ws.title = "Nodes"
    hdr = ["Node", f"X ({len_unit})", f"Y ({len_unit})", f"Z ({len_unit})", "Support", "Tx", "Ty", "Tz", "Rx", "Ry", "Rz"]
    ws.append(hdr)
    for nid in sorted(model.nodes):
        x, y, z = model.nodes[nid]
        # display in model.unit_system
        if model.unit_system == UnitSystem.IMPERIAL:
            x = convert(x, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)
            y = convert(y, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)
            z = convert(z, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)
        sup = model.supports.get(nid, {"type": "FREE"})
        ws.append([nid, round(x, 4), round(y, 4), round(z, 4), sup["type"], sup.get("Tx", 1), sup.get("Ty", 1), sup.get("Tz", 1), sup.get("Rx", 1), sup.get("Ry", 1), sup.get("Rz", 1)])
    for c in ws[1]:
        c.font = header_font; c.fill = header_fill; c.alignment = center; c.border = thin
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions

    # Sheet 2: Members - enhanced with Material/Section
    ws2 = wb.create_sheet("Member Incidences")
    ws2.append(["Member", "Node i", "Node j", f"Length ({len_unit})", "Type", "Material", "Section", f"A ({'mm2' if model.unit_system==UnitSystem.METRIC else 'in2'})", "Beta (deg)", "Release i", "Release j"])
    for m in model.members:
        L_m = member_length_m(model, m)
        L_disp = L_m if model.unit_system == UnitSystem.METRIC else convert(L_m, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)
        sec = model.get_section(m)
        A_disp = sec.A_mm2 if model.unit_system == UnitSystem.METRIC else sec.A_mm2 * CONVERSIONS_REVERSE["in2_to_mm2"]
        # format A
        ws2.append([m.id, m.i, m.j, round(L_disp, 4), m.member_type.value, m.material, m.section, round(A_disp, 2), m.beta_deg, str(m.releases["start"]), str(m.releases["end"])])
    for c in ws2[1]:
        c.font = header_font; c.fill = header_fill; c.alignment = center; c.border = thin
    ws2.freeze_panes = "A2"; ws2.auto_filter.ref = ws2.dimensions

    # Sheet 3: Materials
    ws3 = wb.create_sheet("Materials")
    ws3.append(["Material", "E (MPa)", "E (ksi)", "G (MPa)", "Fy (MPa)", "Fy (ksi)", "alpha (/C)", "alpha (/F)", "density (kg/m3)", "weight (kN/m3)", "weight (pcf)"])
    for name in model.material_library.names():
        mat = model.material_library.get(name)
        if name == "A36": continue  # alias skip duplicate
        ws3.append([name, round(mat.E_MPa, 0), round(mat.E_ksi, 0), round(mat.G_MPa, 0), round(mat.Fy_MPa, 0), round(mat.Fy_ksi, 0), mat.alpha_per_C, mat.alpha_per_F, mat.density_kg_m3, round(mat.weight_kN_m3, 2), round(mat.weight_pcf, 0)])
    for c in ws3[1]:
        c.font = header_font; c.fill = header_fill; c.alignment = center; c.border = thin
    ws3.freeze_panes = "A2"

    # Sheet 4: Sections
    ws4 = wb.create_sheet("Sections")
    ws4.append(["Section", "A (mm2)", "A (in2)", "Iz (mm4)", "Iz (in4)"])
    for name in model.section_library.names():
        if name == "W310x39": continue
        sec = model.section_library.get(name)
        A_in2 = sec.A_mm2 * CONVERSIONS_REVERSE["in2_to_mm2"]
        Iz_in4 = sec.Iz_m4 * 1e12 * CONVERSIONS_REVERSE["in4_to_mm4"]
        ws4.append([name, round(sec.A_mm2, 1), round(A_in2, 2), round(sec.Iz_m4 * 1e12, 0), round(Iz_in4, 1)])
    for c in ws4[1]:
        c.font = header_font; c.fill = header_fill; c.alignment = center; c.border = thin
    ws4.freeze_panes = "A2"

    # Sheet 5: Unit System
    ws5 = wb.create_sheet("Unit System")
    ws5.append(["Item", "Value"])
    ws5.append(["Unit System", model.unit_system.value])
    ws5.append(["Internal length", "m"])
    ws5.append(["Internal force", "kN"])
    ws5.append(["Size internal (m)", round(model.size_m, 4)])
    ws5.append(["Size display", f"{size_display(model):.4f} {len_unit}"])
    for c in ws5["A1:B1"][0]:
        c.font = header_font; c.fill = header_fill; c.alignment = center
    wb.save(filepath)
    return filepath


def size_display(model: Revit3Model) -> float:
    if model.unit_system == UnitSystem.METRIC:
        return model.size_m
    return convert(model.size_m, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)


# ---------------------------------------------------------------------------
# 6. FIGURE (reuse cube.py logic, single file per user choice)
# ---------------------------------------------------------------------------

def _compute_local_axes(nodes: Dict[int, Tuple[float,float,float]], i: int, j: int, beta_deg: float = 0.0):
    """STAAD-like local axes. Reuse logic from python-2/cube.py:139. Requires numpy."""
    import numpy as np
    x1,y1,z1 = nodes[i]; x2,y2,z2 = nodes[j]
    vec = np.array([x2-x1, y2-y1, z2-z1], dtype=float)
    L = float(np.linalg.norm(vec))
    if L < 1e-12:
        raise ValueError("Zero length member")
    x_vec = vec / L
    global_y = np.array([0.0, 1.0, 0.0]); global_z = np.array([0.0, 0.0, 1.0])
    if abs(abs(float(np.dot(x_vec, global_y))) - 1.0) < 1e-6:
        global_x = np.array([1.0, 0.0, 0.0])
        y0 = np.cross(global_z, x_vec)
        if float(np.linalg.norm(y0)) < 1e-9:
            y0 = np.cross(x_vec, global_x)
        y0 = y0 / float(np.linalg.norm(y0))
        z0 = np.cross(x_vec, y0); z0 = z0 / float(np.linalg.norm(z0))
    else:
        z0 = np.cross(x_vec, global_y); z0 = z0 / float(np.linalg.norm(z0))
        y0 = np.cross(z0, x_vec); y0 = y0 / float(np.linalg.norm(y0))
    beta = math.radians(beta_deg)
    cb, sb = math.cos(beta), math.sin(beta)
    y_vec = y0 * cb + z0 * sb; z_vec = -y0 * sb + z0 * cb
    y_vec = y_vec / float(np.linalg.norm(y_vec)); z_vec = z_vec / float(np.linalg.norm(z_vec))
    return {"x": tuple(x_vec), "y": tuple(y_vec), "z": tuple(z_vec), "L": L, "beta": beta_deg}


def create_plot(model: Revit3Model, save_path: str = "rev3_demo.png", show: bool = False, show_local_axes: bool = True, show_dof: bool = True):
    """Single figure (user: single + reuse). Mirrors python-2/cube.py:377 plot_cube but model-driven and unit-aware."""
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3D

    if not os.path.isabs(save_path):
        save_path = os.path.join(os.path.dirname(__file__), save_path)

    # display nodes in model.unit_system units for axes labels (internal is m)
    disp_nodes: Dict[int, Tuple[float,float,float]] = {}
    for nid, (x,y,z) in model.nodes.items():
        if model.unit_system == UnitSystem.IMPERIAL:
            disp_nodes[nid] = (convert(x, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL),
                               convert(y, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL),
                               convert(z, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL))
        else:
            disp_nodes[nid] = (x,y,z)

    len_unit = "ft" if model.unit_system == UnitSystem.METRIC else "m"  # intentionally flipped? fix below
    len_unit = "m" if model.unit_system == UnitSystem.METRIC else "ft"
    # DOF map like cube.py:118
    node_dofs = {nid: [(nid-1)*6 + d + 1 for d in range(6)] for nid in model.nodes}
    SIZE_DISP = size_display(model)

    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")
    xs = [c[0] for c in disp_nodes.values()]; ys = [c[1] for c in disp_nodes.values()]; zs = [c[2] for c in disp_nodes.values()]
    ax.scatter(xs, ys, zs, color="red", s=90, depthshade=False, zorder=5, edgecolors="black", linewidths=0.5)

    for nid, (x,y,z) in disp_nodes.items():
        dofs = node_dofs[nid]
        ax.text(x+0.12*SIZE_DISP/6, y+0.12*SIZE_DISP/6, z+0.12*SIZE_DISP/6, str(nid), fontsize=11, color="darkred", weight="bold")
        if show_dof:
            ax.text(x+0.12*SIZE_DISP/6, y-0.35*SIZE_DISP/6, z+0.12*SIZE_DISP/6, f"({dofs[0]}-{dofs[5]})", fontsize=6, color="dimgray")
        if model.supports.get(nid, {}).get("type") == "PINNED":
            s = 0.9 * SIZE_DISP/6
            base_y = y - 0.7 * SIZE_DISP/6
            corners = [(x-s/2, base_y, z-s/2), (x+s/2, base_y, z-s/2), (x+s/2, base_y, z+s/2), (x-s/2, base_y, z+s/2)]
            for cx,cy,cz in corners: ax.plot([x,cx],[y,cy],[z,cz], color="black", lw=1.2)
            for k in range(4):
                x1,y1,z1=corners[k]; x2,y2,z2=corners[(k+1)%4]
                ax.plot([x1,x2],[y1,y2],[z1,z2], color="black", lw=1.5)
            ax.text(x, base_y-0.15*SIZE_DISP/6, z, "PINNED", fontsize=6, color="black", ha="center", weight="bold")

    # global axes triad (left side, reuse cube.py:408)
    g_len = 1.3 * SIZE_DISP/6
    gx, gy, gz = -1.7*SIZE_DISP/6, 0.4*SIZE_DISP/6, SIZE_DISP/2
    ax.quiver(gx,gy,gz, g_len,0,0, color="red", linewidth=2.2, arrow_length_ratio=0.14)
    ax.quiver(gx,gy,gz, 0,g_len,0, color="green", linewidth=2.2, arrow_length_ratio=0.14)
    ax.quiver(gx,gy,gz, 0,0,g_len, color="blue", linewidth=2.2, arrow_length_ratio=0.14)
    ax.text(gx+g_len+0.15, gy, gz, f"X ({len_unit})", color="red", fontsize=8, weight="bold")
    ax.text(gx, gy+g_len+0.15, gz, f"Y ({len_unit})", color="green", fontsize=8, weight="bold")
    ax.text(gx, gy, gz+g_len+0.15, f"Z ({len_unit})", color="blue", fontsize=8, weight="bold")
    ax.scatter([gx],[gy],[gz], s=40, color="black", zorder=6)

    for m in model.members:
        x1,y1,z1 = disp_nodes[m.i]; x2,y2,z2 = disp_nodes[m.j]
        # color by type (reuse but add material hint)
        if m.member_type == MemberType.COLUMN: color="#1f77b4"
        elif m.member_type == MemberType.ROOF_BEAM: color="#2ca02c"
        else: color="#ff7f0e"
        ax.add_line(Line3D([x1,x2],[y1,y2],[z1,z2], color=color, lw=2.6))
        mx,my,mz=(x1+x2)/2,(y1+y2)/2,(z1+z2)/2
        # label includes section+material (per user: show assignment, not global)
        ax.text(mx,my,mz, f"{m.id}\n{m.section}\n{m.material}", fontsize=5, color="darkgreen", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="green", alpha=0.65))
        if show_local_axes:
            axes = _compute_local_axes(model.nodes, m.i, m.j, m.beta_deg)
            scale = 0.9 * SIZE_DISP/6
            # need disp scale: local axes are unit vectors, same in any system
            ax.quiver(mx,my,mz, axes["x"][0]*scale, axes["x"][1]*scale, axes["x"][2]*scale, color="red", linewidth=1.1, arrow_length_ratio=0.2)
            ax.quiver(mx,my,mz, axes["y"][0]*scale, axes["y"][1]*scale, axes["y"][2]*scale, color="green", linewidth=1.1, arrow_length_ratio=0.2)
            ax.quiver(mx,my,mz, axes["z"][0]*scale, axes["z"][1]*scale, axes["z"][2]*scale, color="blue", linewidth=1.1, arrow_length_ratio=0.2)
        # pinned symbols (tie beams)
        if m.releases.get("start",{}).get("Mz")==1 or m.releases.get("end",{}).get("Mz")==1:
            for (xi,yi,zi) in [(x1,y1,z1),(x2,y2,z2)]:
                # check releases dict: only if this end is pinned; tie beams both ends pinned anyway
                if m.releases.get("start" if (xi==x1 and yi==y1 and zi==z1) else "end",{}).get("Mz")==1:
                    px = xi*0.92 + mx*0.08; py = yi*0.92 + my*0.08; pz = zi*0.92 + mz*0.08
                    ax.scatter([px],[py],[pz], s=70, facecolors="white", edgecolors="orange", linewidths=1.6, marker="o", zorder=6)

    ax.set_xlabel(f"X ({len_unit})")
    ax.set_ylabel(f"Y ({len_unit})")
    ax.set_zlabel(f"Z ({len_unit})")
    lim_pad = SIZE_DISP*0.35
    ax.set_xlim(-2.2*SIZE_DISP/6 - lim_pad/3, SIZE_DISP+1*SIZE_DISP/6)
    ax.set_ylim(-1.5*SIZE_DISP/6, SIZE_DISP+1*SIZE_DISP/6)
    ax.set_zlim(-1*SIZE_DISP/6, SIZE_DISP+1*SIZE_DISP/6)
    ax.set_box_aspect((1,1,1))
    ax.set_title(f"Revit 3 Cube - {model.unit_system.value} ({SIZE_DISP:.2f} {len_unit}) | A36 | Column W12x26 Roof W10x22 Tie W8x18 | PINNED 1-4 | Beta 0 | rev3.py", fontsize=9)
    ax.view_init(elev=22, azim=-35)
    ax.grid(True, alpha=0.3)
    from matplotlib.lines import Line2D
    legend_elems=[
        Line2D([0],[0], marker='o', color='w', markerfacecolor='red', markeredgecolor='black', markersize=8, label='Nodes 1-8'),
        Line2D([0],[0], color='#1f77b4', lw=2.6, label='Column M9-M12 (ASTM A36 / W12x26)'),
        Line2D([0],[0], color='#2ca02c', lw=2.6, label='Roof M5-M8 (ASTM A36 / W10x22)'),
        Line2D([0],[0], color='#ff7f0e', lw=2.6, label='Tie M1-M4 (ASTM A36 / W8x18, Mz pinned)'),
        Line2D([0],[0], color='red', lw=2, label='Local/global X'),
        Line2D([0],[0], color='green', lw=2, label='Local/global Y'),
        Line2D([0],[0], color='blue', lw=2, label='Local/global Z'),
    ]
    ax.legend(handles=legend_elems, loc="upper left", bbox_to_anchor=(0.02,0.98), fontsize=7, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return save_path

# ---------------------------------------------------------------------------
# Demo / validation
# ---------------------------------------------------------------------------

def _demo():
    print("=== Revit 3 Solver Update - rev3.py demo ===")
    print(f"Units base: inch_to_mm={BASE['inch_to_mm']}, lbf_to_N={BASE['lbf_to_N']}")
    print(f"Conversions: ft->m={CONVERSIONS['ft_to_m']:.6f}, ksi->MPa={CONVERSIONS['ksi_to_MPa']:.6f}")
    # Metric
    m_metric = create_revit3_cube(unit_system=UnitSystem.METRIC, size=6.0)
    print("\n--- METRIC (6 m) ---")
    print(m_metric.summary())
    m_metric.validate()
    print("validate: OK")
    # Imperial 19.685 ft == 6 m
    m_imp = create_revit3_cube(unit_system=UnitSystem.IMPERIAL, size=6.0 / CONVERSIONS["ft_to_m"])
    print(f"\n--- IMPERIAL ({6.0/CONVERSIONS['ft_to_m']:.4f} ft == 6 m) ---")
    print(m_imp.summary())
    print(f"Imperial internal size_m={m_imp.size_m:.6f} m (should be 6.0)")
    assert abs(m_imp.size_m - 6.0) < 1e-9
    # Round-trip
    ft_val = 6.0
    m_val = convert(ft_val, "length_ft_m", UnitSystem.IMPERIAL, UnitSystem.METRIC)
    ft_back = convert(m_val, "length_ft_m", UnitSystem.METRIC, UnitSystem.IMPERIAL)
    assert abs(ft_back - ft_val) < 1e-9
    print(f"Round-trip ft->m->ft: {ft_val}->{m_val:.6f}->{ft_back:.6f} OK")
    # Per-member distinct section
    custom = create_revit3_cube(unit_system=UnitSystem.METRIC, sections={MemberType.COLUMN: "W12x26", MemberType.ROOF_BEAM: "W10x22", MemberType.TIE_BEAM: "W8x18"})
    assert custom.members[0].section == "W8x18"  # M1 tie
    assert custom.members[4].section == "W10x22"  # M5 roof
    assert custom.members[8].section == "W12x26"  # M9 column
    print("Per-member section distinct: TIE W8x18 / ROOF W10x22 / COLUMN W12x26 OK")
    # Material all A36 but not global
    for mem in custom.members:
        assert mem.material == "ASTM A36"
    print("Material per-member A36 OK")
    # Validation rejection
    try:
        create_revit3_cube(unit_system=UnitSystem.METRIC, sections={MemberType.COLUMN: "UNKNOWN"})
        raise AssertionError("should have raised UnknownSectionError")
    except UnknownSectionError as e:
        print(f"Unknown section rejection OK: {e}")
    try:
        bad = create_revit3_cube()
        bad.members[0].material = "UNKNOWN_MAT"
        bad.validate()
        raise AssertionError("should have raised UnknownMaterialError")
    except UnknownMaterialError as e:
        print(f"Unknown material rejection OK: {e}")
    try:
        validate_unit_system("BOGUS")
        raise AssertionError("should have raised")
    except ValueError as e:
        print(f"Invalid unit system rejection OK: {e}")
    # A36 values cross-check vs Converter sheet
    mat = m_metric.material_library.get("ASTM A36")
    print(f"\nA36 E={mat.E_MPa:.0f} MPa / {mat.E_ksi:.0f} ksi (Converter expects 199948 MPa for 29000 ksi)")
    assert 199000 < mat.E_MPa < 201000
    assert abs(mat.weight_pcf - 490) < 5
    print("A36 cross-check OK")
    # Length conversion display
    print(f"\nTie M1 length internal {member_length_m(m_metric, m_metric.members[0]):.2f} m = {convert(member_length_m(m_metric, m_metric.members[0]), 'length_ft_m', UnitSystem.METRIC, UnitSystem.IMPERIAL):.4f} ft")
    print("\nDemo complete - all validations PASS")
    # diagram
    print("""
        Roof Beam (M5-M8)
    .----------------.  M5 6m top
    |                |
 Column M9-M12   Column  6m vertical
    |                |
    .----------------.
        Tie Beam (M1-M4) 6m bottom
 All: ASTM A36, per-member section, selectable Imperial/Metric
    """)


if __name__ == "__main__":
    import argparse, os, sys
    ap = argparse.ArgumentParser(description="Rev3 Revit 3 Cube Demo")
    ap.add_argument("--excel", action="store_true", help="write rev3_demo.xlsx (single, metric default)")
    ap.add_argument("--plot", action="store_true", help="also render single figure rev3_demo.png (reuse cube.py logic)")
    ap.add_argument("--no-show", action="store_true", help="headless: save PNG without plt.show() (default shows when --plot)")
    ap.add_argument("--imperial", action="store_true", help="use IMPERIAL ft for demo/exports instead of METRIC m")
    args = ap.parse_args()
    _demo()
    # default bare run (no flags) now also shows figure for interactive use - user expected figure on `py rev3.py`
    if not args.excel and not args.plot:
        args.plot = True  # bare `python rev3.py` pops figure (shows)
    if args.excel or args.plot:
        unit = UnitSystem.IMPERIAL if args.imperial else UnitSystem.METRIC
        size = 6.0 if unit == UnitSystem.METRIC else 6.0 / CONVERSIONS["ft_to_m"]
        m = create_revit3_cube(unit, size=size)
        if args.excel:
            p = create_excel(m, "rev3_demo.xlsx")
            print(f"Excel written: {p} ({unit.value})")
        if args.plot:
            # default: show window unless --no-show headless
            show = not args.no_show
            # force non-blocking backend check: use TkAgg if available
            pp = create_plot(m, "rev3_demo.png", show=show)
            print(f"Figure written: {pp} ({unit.value}, show={show})")
            if show:
                print("Figure window opened - close it to exit.")
            else:
                print("Headless: PNG saved, not shown (use without --no-show to pop window).")
