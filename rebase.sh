#!/bin/bash
# This scripts rebases each of the versioned branches (branches starting with "2.")
# so that is has the same code as the main branch, plus an additional commit
# that sets the libxml2 version for that branch.

set -eo pipefail

old_branch=$(git symbolic-ref --short HEAD)
trap 'git checkout "$old_branch"' EXIT ERR

git for-each-ref --format='%(refname:short)' --exclude refs/heads/main 'refs/heads/2\.*' | while read -r branch; do
    git checkout "$branch"
    commit=$(git show-ref -s "refs/heads/$branch")
    git reset --hard refs/heads/main
    git cherry-pick "$commit" || git cherry-pick --abort
    git push -f origin HEAD
done

