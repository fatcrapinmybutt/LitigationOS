#!/usr/bin/env bash
set -euo pipefail

# import_repos.sh
#
# Clone each source repository and copy its working tree (no .git) into
# imports/<repo-name>/ inside the current repository. Intended to be run
# locally or on a CI runner that has push access to the target repository.

REPOS=(
  "fatcrapinmybutt/fredprime-legal-system"
  "fatcrapinmybutt/FRAUD"
  "fatcrapinmybutt/the_manbearpig"
  "fatcrapinmybutt/CourtRules"
  "fatcrapinmybutt/MICHIGAN-HIGHER-COURTS"
  "fatcrapinmybutt/Michigan-MCLA"
)

WORKDIR=$(mktemp -d)
echo "Using temporary workdir: $WORKDIR"

mkdir -p imports

for repo in "${REPOS[@]}"; do
  name=$(basename "$repo")
  tmpdir="$WORKDIR/$name"
  echo "\n---\nProcessing $repo -> imports/$name"
  git clone --depth=1 "https://github.com/$repo.git" "$tmpdir"
  # Remove any existing import dir to ensure a clean copy
  rm -rf "imports/$name"
  mkdir -p "imports/$name"
  # Use rsync to preserve file mode & handle binary files; exclude .git
  rsync -a --exclude='.git' --delete "$tmpdir/" "imports/$name/"
  # Optionally save a snapshot as a tarball archive
  # tar -C "$tmpdir" -czf "11_ARCHIVES/${name}-snapshot.tar.gz" . --exclude='.git'
  rm -rf "$tmpdir"
done

# Cleanup
rm -rf "$WORKDIR"

echo "\nAll repos copied to imports/. Review the changes, then commit and push this branch:\n"
echo "  git add imports/ && git commit -m \"chore(merge): import repositories into imports/\" && git push origin merge/all-repos-2026-06-28"
