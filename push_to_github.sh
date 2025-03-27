#!/bin/bash

# This script helps push your code to GitHub
# Usage: bash push_to_github.sh your-github-username your-repo-name

# Check if username and repo name are provided
if [ $# -ne 2 ]; then
    echo "Usage: bash push_to_github.sh your-github-username your-repo-name"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME=$2

# Initialize git repository if it doesn't exist
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Add all files to git
echo "Adding files to git..."
git add .

# Create a commit
echo "Creating commit..."
git commit -m "Initial commit of Telegram Message Forwarder"

# Add GitHub remote
echo "Adding GitHub remote..."
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
# In case the remote already exists, set-url instead
git remote set-url origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Push to GitHub
echo "Pushing to GitHub..."
echo "You will be prompted for your GitHub username and password/token."
git push -u origin master

echo "Done! Your code is now on GitHub at: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "You can now deploy it on Koyeb."