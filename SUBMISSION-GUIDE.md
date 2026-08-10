# Submission Guide — Numerical Method 2026, Section B

You do not need to install Git, and you do not need to use a command line.
Everything below is done in a web browser.

---

## Once, at the start of the semester

1. **Fork this repository.** Click **Fork** at the top right of the repository
   page, then **Create fork**. You now have your own copy at
   `github.com/<your-username>/Numerical-Method-2026-Section-B`.

2. **Create your folder.** In your fork, open the `submissions/` folder and
   click **Add file → Create new file**. In the file-name box type:

   ```
   surname-firstname/README.md
   ```

   Typing a `/` creates the folder. Put your name and student number in the
   file, then **Commit new file**.

   Use lower case and hyphens: `delacruz-juan`, not `Dela Cruz, Juan`.

---

## For every assignment

1. In **your fork**, go to `submissions/surname-firstname/`.

2. **Add file → Create new file**, and type `lab01/README.md` to create the
   folder for that laboratory. Commit it.

3. Open the new `lab01/` folder and choose **Add file → Upload files**. Drag in
   everything the assignment asks for. For Laboratory 1 that is:

   ```
   lab01_<surname>.py               your code
   lab01_report_<surname>.pdf       your write-up
   lab01_ai_prompts_<surname>.docx  your AI Prompt Log
   lab01_output_<surname>.txt       the console output
   figures/                          your PNG figures
   ```

   The exact list is on the assignment page under **Expected file
   deliverables**. Do not rename anything.

4. Write a commit message that says what it is, for example
   `Lab 01 submission - Dela Cruz`. Then **Commit changes**.

5. **Open a pull request.** Go to the **Pull requests** tab of your fork, click
   **New pull request**, then **Create pull request**. Title it:

   ```
   Section B - Lab 01 - Dela Cruz, Juan
   ```

   The timestamp on that pull request is your submission time.

6. If you need to correct something before the deadline, upload the corrected
   file to the same folder. The pull request updates itself; you do not open a
   second one.

---

## What counts as submitted

The pull request. Not the commit, not an e-mail, not a message. If no pull
request exists, nothing was submitted.

Late work is accepted with the standing deduction of 10 % per day, to a floor
of 40 %. The pull request timestamp is what is used, and it cannot be edited.

---

## Common mistakes

| Mistake | What happens |
|---|---|
| Files placed in the repository root instead of your folder | The pull request is closed unmerged and the work is marked late until it is fixed. |
| Renaming files "to make them tidier" | Marked as a missing deliverable. |
| Uploading a `.zip` instead of the individual files | The point of the repository is that the marker can read your code in the browser. Upload the files. |
| Editing `materials/` | Treated as academic dishonesty. |
| Forgetting `figures/` | Standing deduction for unlabelled or missing figures. |
| Notebook (`.ipynb`) instead of `.py` | Not an accepted deliverable. Export to `.py` first. |

---

## If something goes wrong

Open an **Issue** on the main repository and paste the exact error message as
text. "It does not work" cannot be diagnosed;
`ModuleNotFoundError: No module named 'scipy'` can be fixed in ten seconds.

---

*Prepared by Engr. Escranda.*
