# GitHub Upload Plan

Final repository name: `dynamic-limits-growth-ukf`

GitHub description: System-dynamics-informed macro-financial stress analysis using a nonlinear state-space model estimated with an Unscented Kalman Filter on post-2003 U.S. data.

Initial commit message: `Initial research-code release for Dynamic Limits of Growth UKF model`

## Upload sequence

1. Create a new empty GitHub repository named `dynamic-limits-growth-ukf`.
2. Extract `dynamic-limits-growth-ukf_GITHUB_READY.zip`.
3. Open a terminal in the extracted `dynamic-limits-growth-ukf/` folder.
4. Run `git init`.
5. Run `git status` and confirm excluded files are not staged.
6. Run `git add README.md LICENSE requirements.txt .gitignore GITHUB_UPLOAD_PLAN.md PROJECT_MANIFEST.csv data/ docs/ notebooks/ results/README.md`.
7. Run `git commit -m "Initial research-code release for Dynamic Limits of Growth UKF model"`.
8. Add the GitHub remote.
9. Push only after final manual review.

## Do not upload

- raw bulk data dumps unless redistribution rights are clear
- old UKF run folders
- generated ZIP packs
- LaTeX temporary files
- logs, `.aux`, `.fls`, `.fdb_latexmk`
- private documents, application materials, CVs, letters, transcripts, email exports, or credentials
