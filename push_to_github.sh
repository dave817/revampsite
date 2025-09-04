#!/bin/bash

# GitHub username
GITHUB_USERNAME="dave817"

echo "Setting up GitHub remote..."
git remote add origin git@github.com:${GITHUB_USERNAME}/revampsite.git

echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✅ Successfully pushed to GitHub!"
echo "Visit: https://github.com/${GITHUB_USERNAME}/revampsite"