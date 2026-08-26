"""
CUBE_Rev1.py
================================================================================
6m x 6m x 6m Cube Structure - Structural Model Builder  (Rev. 1)
================================================================================
Rev. 1 changes (relative to the original CUBE.py):
    1. Support conditions added at the bottom (Y = 0) nodes -> Pinned supports
    2. Beta angle added for every member (rotation of local y-z about local x)
    3. Local axes (x,y,z) computed for every member + global axes shown on plot
    4. Degrees of Freedom (DOF) numbered for every node (6 DOF/node: 3 trans + 3 rot)
    5. Member end-release DOFs added (pinned/hinged beam ends release moments,
       e.g. torsion about local-x and bending about local-z)
    6. Pinned (hinge) symbol drawn on the 3D diagram wherever a moment release exists
    7. 3D structural diagram updated: supports, local axes triads, global axes
       triad, and pin symbols all shown together with nodes/members
    8. Excel workbook updated with new tabs: Node DOF Table, Support Conditions,
       Member Local Axes & Beta Angles, Member End Releases

Author: Rev. 1 update
================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend so the script can run headless
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D projection)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import openpyxl
from openpyxl import Workbook

# ==============================================================================
# 1. GEOMETRY DEFINITION
# ==============================================================================
# Node coordinates (X, Y, Z) in meters.  Y is the VERTICAL axis in this model.
nodes = {
    1: [0, 0, 0],     # Bottom front left   (Y = 0 -> ground level)
    2: [6, 0, 0],     # Bottom front right   (Y = 0 -> ground level)
    3: [6, 0, 6],     # Bottom back right    (Y = 0 -> ground level)
    4: [0, 0, 6],     # Bottom back left     (Y = 0 -> ground level)
    5: [0, 6, 0],     # Top front left
    6: [6, 6, 0],     # Top front right
    7: [6, 6, 6],     # Top back right
    8: [0, 6, 6]      # Top back left
}

# Members (i, j) = (start node, end node)
members = {
    'M1': [1, 2],   # Bottom front
    'M2': [2, 3],   # Bottom right
    'M3': [3, 4],   # Bottom back
    'M4': [4, 1],   # Bottom left
    'M5': [5, 6],   # Top front
    'M6': [6, 7],   # Top right
    'M7': [7, 8],   # Top back
    'M8': [8, 5],   # Top left
    'M9': [1, 5],   # Vertical front left
    'M10': [2, 6],  # Vertical front right
    'M11': [3, 7],  # Vertical back right
    'M12': [4, 8]   # Vertical back left
}

# ==============================================================================
# 2. SUPPORT CONDITIONS  (Feature 1)
# ==============================================================================
# Bottom nodes (Y = 0) are given PINNED supports:
#   Translations UX, UY, UZ  -> RESTRAINED (fixed = 1)
#   Rotations    RX, RY, RZ  -> FREE       (released = 0)
SUPPORT_NODES = [n for n, (x, y, z) in nodes.items() if y == 0]

support_conditions = {}
for n in nodes:
    if n in SUPPORT_NODES:
        support_conditions[n] = {
            'Type': 'Pinned',
            'UX': 'Fixed', 'UY': 'Fixed', 'UZ': 'Fixed',
            'RX': 'Free', 'RY': 'Free', 'RZ': 'Free'
        }
    else:
        support_conditions[n] = {
            'Type': 'Free (no support)',
            'UX': 'Free', 'UY': 'Free', 'UZ': 'Free',
            'RX': 'Free', 'RY': 'Free', 'RZ': 'Free'
        }

# ==============================================================================
# 3. DEGREES OF FREEDOM (DOF) NUMBERING  (Feature 4)
# ==============================================================================
# Each node has 6 DOF (space-frame element): UX, UY, UZ, RX, RY, RZ
DOF_LABELS = ['UX', 'UY', 'UZ', 'RX', 'RY', 'RZ']
node_dof = {}
for n in sorted(nodes.keys()):
    base = (n - 1) * 6
    node_dof[n] = {label: base + k + 1 for k, label in enumerate(DOF_LABELS)}

# ==============================================================================
# 4. BETA ANGLE  (Feature 2)
# ==============================================================================
# Beta angle (deg) rotates the member's local y-z axes about its own local-x
# (longitudinal) axis, exactly like RISA/STAAD's "orientation angle".
# Default = 0 deg for all members. Edit individual values below as needed.
beta_angle = {m: 0.0 for m in members}
# Example: give the vertical columns a 45 deg beta angle to demonstrate the feature
beta_angle['M9'] = 45.0
beta_angle['M10'] = 45.0
beta_angle['M11'] = 45.0
beta_angle['M12'] = 45.0

# ==============================================================================
# 5. MEMBER END RELEASES / PINNED BEAM DOF  (Feature 5)
# ==============================================================================
# A member can be "pinned" (hinged) at either end, releasing rotational DOF so
# no moment is transferred through that release.  Per project requirement, a
# pinned beam releases:
#     - Moment about local-X (torsion, RX)   at the start (i) end
#     - Moment about local-Z (minor/major bending, RZ) at the end (j) end
# All other members remain fully moment-connected (rigid) by default.
PINNED_MEMBERS = ['M5', 'M6', 'M7', 'M8']   # top-face beams modeled as pinned

member_releases = {}
for m in members:
    if m in PINNED_MEMBERS:
        member_releases[m] = {
            'Pinned': True,
            'i_release': {'RX'},   # torsion released at start node
            'j_release': {'RZ'}    # bending about local-z released at end node
        }
    else:
        member_releases[m] = {
            'Pinned': False,
            'i_release': set(),
            'j_release': set()
        }

# ==============================================================================
# 6. LOCAL AXES  (Feature 3)
# ==============================================================================
GLOBAL_VERTICAL = np.array([0.0, 1.0, 0.0])   # Global Y is "up" in this model
GLOBAL_Z_REF = np.array([0.0, 0.0, 1.0])


def rotate_about_axis(vec, axis, angle_deg):
    """Rotate vector `vec` about unit vector `axis` by angle_deg (Rodrigues' formula)."""
    theta = np.radians(angle_deg)
    axis = axis / np.linalg.norm(axis)
    return (vec * np.cos(theta)
            + np.cross(axis, vec) * np.sin(theta)
            + axis * np.dot(axis, vec) * (1 - np.cos(theta)))


def compute_local_axes(i_coord, j_coord, beta_deg):
    """
    Returns (local_x, local_y, local_z) unit vectors for a member from i to j,
    following the standard STAAD/RISA convention:
      - local_x runs along the member (i -> j)
      - a reference "up" vector (global Y) is used to build local_z, unless the
        member itself is vertical (parallel to global Y), in which case global Z
        is used as the reference instead
      - beta angle then rotates local_y / local_z about local_x
    """
    p_i, p_j = np.array(i_coord, dtype=float), np.array(j_coord, dtype=float)
    local_x = p_j - p_i
    local_x = local_x / np.linalg.norm(local_x)

    if abs(np.dot(local_x, GLOBAL_VERTICAL)) > 0.999:  # member is vertical
        ref = GLOBAL_Z_REF
    else:
        ref = GLOBAL_VERTICAL

    local_z = np.cross(local_x, ref)
    local_z = local_z / np.linalg.norm(local_z)
    local_y = np.cross(local_z, local_x)
    local_y = local_y / np.linalg.norm(local_y)

    # Apply beta-angle rotation of y/z about x
    if beta_deg:
        local_y = rotate_about_axis(local_y, local_x, beta_deg)
        local_z = rotate_about_axis(local_z, local_x, beta_deg)

    return local_x, local_y, local_z


member_local_axes = {}
for m, (i, j) in members.items():
    lx, ly, lz = compute_local_axes(nodes[i], nodes[j], beta_angle[m])
    member_local_axes[m] = {'local_x': lx, 'local_y': ly, 'local_z': lz}

# ==============================================================================
# 7. DATAFRAMES FOR EXCEL EXPORT
# ==============================================================================
nodes_df = pd.DataFrame.from_dict(nodes, orient='index', columns=['X (m)', 'Y (m)', 'Z (m)'])
nodes_df.index.name = 'Node'

members_data = []
for member_name, (i, j) in members.items():
    members_data.append({
        'Member': member_name,
        'Start Node (i)': i,
        'End Node (j)': j,
        'Start X': nodes[i][0], 'Start Y': nodes[i][1], 'Start Z': nodes[i][2],
        'End X': nodes[j][0], 'End Y': nodes[j][1], 'End Z': nodes[j][2]
    })
members_df = pd.DataFrame(members_data).set_index('Member')

summary_data = []
for node_id, (x, y, z) in nodes.items():
    connected_members = [m for m, (i, j) in members.items() if i == node_id or j == node_id]
    summary_data.append({
        'Node': node_id, 'X (m)': x, 'Y (m)': y, 'Z (m)': z,
        'Connected Members': ', '.join(connected_members)
    })
summary_df = pd.DataFrame(summary_data).set_index('Node')

# --- Node DOF table ---
dof_rows = []
for n in sorted(nodes.keys()):
    row = {'Node': n}
    row.update(node_dof[n])
    dof_rows.append(row)
node_dof_df = pd.DataFrame(dof_rows).set_index('Node')

# --- Support conditions table ---
support_rows = []
for n in sorted(nodes.keys()):
    row = {'Node': n}
    row.update(support_conditions[n])
    support_rows.append(row)
support_df = pd.DataFrame(support_rows).set_index('Node')

# --- Member local axes & beta angle table ---
axes_rows = []
for m in members:
    lx, ly, lz = member_local_axes[m]['local_x'], member_local_axes[m]['local_y'], member_local_axes[m]['local_z']
    axes_rows.append({
        'Member': m,
        'Beta Angle (deg)': beta_angle[m],
        'Local X (i,j,k)': f"({lx[0]:.3f}, {lx[1]:.3f}, {lx[2]:.3f})",
        'Local Y (i,j,k)': f"({ly[0]:.3f}, {ly[1]:.3f}, {ly[2]:.3f})",
        'Local Z (i,j,k)': f"({lz[0]:.3f}, {lz[1]:.3f}, {lz[2]:.3f})"
    })
axes_df = pd.DataFrame(axes_rows).set_index('Member')

# --- Member end releases table ---
release_rows = []
for m in members:
    r = member_releases[m]
    release_rows.append({
        'Member': m,
        'Pinned?': 'Yes' if r['Pinned'] else 'No',
        'Start (i) Releases': ', '.join(sorted(r['i_release'])) if r['i_release'] else 'None (Rigid)',
        'End (j) Releases': ', '.join(sorted(r['j_release'])) if r['j_release'] else 'None (Rigid)'
    })
releases_df = pd.DataFrame(release_rows).set_index('Member')

# ==============================================================================
# 8. WRITE EXCEL WORKBOOK  (Feature 8)
# ==============================================================================
output_file = 'cube_structure_6m_Rev1.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    nodes_df.to_excel(writer, sheet_name='Nodes')
    members_df.to_excel(writer, sheet_name='Member Incidences')
    summary_df.to_excel(writer, sheet_name='Node Summary')
    node_dof_df.to_excel(writer, sheet_name='Node DOF Table')
    support_df.to_excel(writer, sheet_name='Support Conditions')
    axes_df.to_excel(writer, sheet_name='Local Axes & Beta Angle')
    releases_df.to_excel(writer, sheet_name='Member End Releases')

print(f"Excel file '{output_file}' created successfully with all Rev.1 tabs.")

# ==============================================================================
# 9. 3D STRUCTURAL DIAGRAM  (Features 3, 6, 7)
# ==============================================================================
fig = plt.figure(figsize=(14, 12))
ax = fig.add_subplot(111, projection='3d')

# --- Plot nodes ---
for node_id, (x, y, z) in nodes.items():
    ax.scatter(x, y, z, color='red', s=90, zorder=5)
    ax.text(x, y, z, f'  N{node_id}', fontsize=9, fontweight='bold')

# --- Plot members ---
for member_name, (i, j) in members.items():
    x1, y1, z1 = nodes[i]
    x2, y2, z2 = nodes[j]
    ax.plot([x1, x2], [y1, y2], [z1, z2],
             color='blue', linewidth=2, marker='o', markersize=5, zorder=2)
    mid_x, mid_y, mid_z = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
    ax.text(mid_x, mid_y, mid_z, f'  {member_name}', fontsize=8, color='green', fontweight='bold')

# --- Support symbols (Feature 1): pinned triangle at restrained bottom nodes ---
support_size = 1.1
for n in SUPPORT_NODES:
    x, y, z = nodes[n]
    # Simple 3D triangle "pin support" symbol pointing down from the node
    tri = np.array([
        [x, y, z],
        [x - support_size / 2, y - support_size, z - support_size / 2],
        [x + support_size / 2, y - support_size, z + support_size / 2]
    ])
    poly = Poly3DCollection([tri], facecolor='orange', edgecolor='black', alpha=0.85, zorder=4)
    ax.add_collection3d(poly)
ax.scatter([], [], [], color='orange', marker='^', s=80, label='Pinned Support')

# --- Local axes triads at member midpoints (Feature 3) ---
axis_len = 1.0
for member_name, (i, j) in members.items():
    x1, y1, z1 = nodes[i]
    x2, y2, z2 = nodes[j]
    mid = np.array([(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2])
    lx = member_local_axes[member_name]['local_x']
    ly = member_local_axes[member_name]['local_y']
    lz = member_local_axes[member_name]['local_z']
    ax.quiver(*mid, *(lx * axis_len), color='red', linewidth=1.3, arrow_length_ratio=0.3, zorder=6)
    ax.quiver(*mid, *(ly * axis_len), color='limegreen', linewidth=1.3, arrow_length_ratio=0.3, zorder=6)
    ax.quiver(*mid, *(lz * axis_len), color='purple', linewidth=1.3, arrow_length_ratio=0.3, zorder=6)

# --- Global axes triad (Feature 3), placed at an offset corner so it doesn't overlap the cube ---
origin = np.array([-2.0, -2.0, -1.0])
g_len = 2.0
ax.quiver(*origin, g_len, 0, 0, color='black', linewidth=2, arrow_length_ratio=0.2)
ax.text(*(origin + [g_len * 1.1, 0, 0]), 'X (global)', fontsize=9, fontweight='bold')
ax.quiver(*origin, 0, g_len, 0, color='black', linewidth=2, arrow_length_ratio=0.2)
ax.text(*(origin + [0, g_len * 1.1, 0]), 'Y (global)', fontsize=9, fontweight='bold')
ax.quiver(*origin, 0, 0, g_len, color='black', linewidth=2, arrow_length_ratio=0.2)
ax.text(*(origin + [0, 0, g_len * 1.1]), 'Z (global)', fontsize=9, fontweight='bold')

# --- Pin (hinge) symbols at released member ends (Feature 6) ---
pin_offset = 0.5
pin_plotted_label = False
for member_name, (i, j) in members.items():
    r = member_releases[member_name]
    if not r['Pinned']:
        continue
    p_i, p_j = np.array(nodes[i], dtype=float), np.array(nodes[j], dtype=float)
    direction = (p_j - p_i) / np.linalg.norm(p_j - p_i)

    if r['i_release']:
        pin_pt = p_i + direction * pin_offset
        ax.scatter(*pin_pt, facecolor='white', edgecolor='magenta', s=110, linewidth=1.8,
                   zorder=7, label='Pinned (Moment Release)' if not pin_plotted_label else None)
        pin_plotted_label = True
    if r['j_release']:
        pin_pt = p_j - direction * pin_offset
        ax.scatter(*pin_pt, facecolor='white', edgecolor='magenta', s=110, linewidth=1.8,
                   zorder=7, label='Pinned (Moment Release)' if not pin_plotted_label else None)
        pin_plotted_label = True

# --- Axis labels, title, limits ---
ax.set_xlabel('X (m)', fontsize=12, labelpad=10)
ax.set_ylabel('Y (m) - Vertical', fontsize=12, labelpad=10)
ax.set_zlabel('Z (m)', fontsize=12, labelpad=10)
ax.set_title('6m x 6m x 6m Cube Structure - Rev. 1\n'
             'Supports, Local/Global Axes, DOF & Pin Releases', fontsize=13, fontweight='bold')

ax.set_xlim([-3, 8])
ax.set_ylim([-3, 8])
ax.set_zlim([-2, 8])
ax.grid(True, alpha=0.3)
ax.view_init(elev=22, azim=-50)

# Manual legend proxies for local-axis colors + existing symbol handles
from matplotlib.lines import Line2D
legend_handles = [
    Line2D([0], [0], color='orange', marker='^', linestyle='None', markersize=10, label='Pinned Support'),
    Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='white',
           markeredgecolor='magenta', markersize=9, label='Pinned (Moment Release)'),
    Line2D([0], [0], color='red', lw=2, label='Local X axis'),
    Line2D([0], [0], color='limegreen', lw=2, label='Local Y axis'),
    Line2D([0], [0], color='purple', lw=2, label='Local Z axis'),
]
ax.legend(handles=legend_handles, loc='upper left', fontsize=8)

plt.tight_layout()
plt.savefig('cube_structure_3d_Rev1.png', dpi=300, bbox_inches='tight')
print("3D diagram saved as 'cube_structure_3d_Rev1.png'")
plt.close(fig)

# ==============================================================================
# 10. CONSOLE SUMMARY
# ==============================================================================
print("\n" + "=" * 70)
print("CUBE STRUCTURE SUMMARY - Rev. 1")
print("=" * 70)
print(f"Total Nodes: {len(nodes)}")
print(f"Total Members: {len(members)}")
print(f"Cube Dimensions: 6m x 6m x 6m")
print(f"DOF per Node: 6 (UX, UY, UZ, RX, RY, RZ)  ->  Total structure DOF: {len(nodes) * 6}")
print(f"Support Nodes (Pinned): {SUPPORT_NODES}")
print(f"Pinned (Hinged) Members: {PINNED_MEMBERS}")
print("=" * 70)

print("\nNode DOF Table:")
print(node_dof_df)
print("\nSupport Conditions:")
print(support_df)
print("\nLocal Axes & Beta Angle:")
print(axes_df)
print("\nMember End Releases:")
print(releases_df)
