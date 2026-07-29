#!/usr/bin/env bash
# ==============================================================================
# FEATURESTIC LEAKS - REPOSITORY CLEANUP & GIT EXPORT SCRIPT FOR TERMUX
# ==============================================================================

echo "🧹 Cleaning repository: Removing Web UI files, keeping ONLY Termux scripts..."

# 1. Forcefully remove web application files and folders
rm -rf assets public src index.html metadata.json .env.example vite.config.ts tsconfig.json tsconfig.node.json components.json package.json package-lock.json

# 2. Stage all changes including deletions
git add -A

# 3. Commit clean state
git commit -m "Removed Web UI and kept Termux files only"

# 4. Push cleanly to GitHub main branch
git push origin main

echo "✅ Clean Termux Repository Pushed Successfully to GitHub!"
