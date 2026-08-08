# Step 87: unified step closer and atomic CHANGE.LOG update

This step replaces the fragmented tarball, executor, changelog, test, commit, and push workflow with one guarded command.

For each future step, `git-pipeline.sh <n>` now:

1. reads `/Users/tom/Downloads/video-forensics-step-<n>.tar.gz`
2. validates and extracts it into `/Users/tom/projects/video-forensics`
3. removes the downloaded tarball
4. runs the standardized one-time executor `integrate_step.py`
5. removes the executor only after successful integration
6. reads `STEP_<n>.md`
7. atomically prepends its exact content to `CHANGE.LOG`
8. removes `STEP_<n>.md`
9. runs Ruff with fixes, pytest, and `git diff --check`
10. stages, commits as `Next Step`, and pushes

Tar extraction rejects absolute paths, parent traversal, links, and device entries. CHANGE.LOG replacement is atomic and refuses duplicate `# Step <n>:` entries. The retired `make_changelog.py` now fails explicitly instead of modifying project history.
