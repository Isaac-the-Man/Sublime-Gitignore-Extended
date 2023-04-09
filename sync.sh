#!/bin/bash

# sync template .gitignore files with remote repo
git submodule  update --init --recursive --remote

# delete local folder
rm -rf DefaultGitignoreTemplates

# copy updated files to local folder
rsync -zarv --prune-empty-dirs --include="*/" --include="*.gitignore" --exclude="*" "gitignore/" "DefaultGitignoreTemplates"