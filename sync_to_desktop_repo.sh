#!/bin/zsh
# Syncs the staged add-on source + docs into the git repo at ~/Desktop/anki_stuff
# and commits. Run this once Desktop access is available (it was blocked by a
# macOS privacy/TCC denial when the files were staged here).
set -e
REPO="$HOME/Desktop/anki_stuff"
STAGE="$HOME/Documents/anki_stuff_staging"

ls "$REPO" > /dev/null  # fails fast if Desktop is still TCC-blocked

mkdir -p "$REPO/french_llm_grader"
cp "$STAGE"/french_llm_grader/*.{py,json,md} "$REPO/french_llm_grader/"
cp "$STAGE/anki-llm-grader-implementation-notes.md" "$REPO/"

cd "$REPO"
git add french_llm_grader anki-llm-grader-implementation-notes.md
git commit -m "Add French LLM Grader add-on and implementation notes

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
echo "Synced and committed."
