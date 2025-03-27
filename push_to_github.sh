#!/bin/bash

# This script helps push your code to GitHub
# Usage: bash push_to_github.sh your-github-username your-repo-name

# Function to show help message
show_help() {
    echo "Telegram Advanced Message Forwarder - GitHub Push Script"
    echo ""
    echo "This script helps you push your code to GitHub for deployment on various platforms"
    echo "such as Koyeb, Heroku, Railway, Replit, or a VPS."
    echo ""
    echo "Usage: bash push_to_github.sh your-github-username your-repo-name [branch]"
    echo ""
    echo "Parameters:"
    echo "  your-github-username    Your GitHub username"
    echo "  your-repo-name          Your GitHub repository name"
    echo "  branch                  The branch to push to (default: main)"
    echo ""
    echo "Example:"
    echo "  bash push_to_github.sh johnsmith telegram-forwarder"
    echo ""
    echo "Note: You will need to enter your GitHub credentials when prompted."
    echo "Using a personal access token is recommended instead of password."
    echo ""
    echo "Visit https://github.com/settings/tokens to create a token with 'repo' scope."
}

# Check if help is requested
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

# Check if username and repo name are provided
if [ $# -lt 2 ]; then
    echo "Error: Missing required parameters."
    echo "Usage: bash push_to_github.sh your-github-username your-repo-name [branch]"
    echo "Use --help for more information."
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME=$2
BRANCH=${3:-main}  # Default to main if not specified

echo "================================================================"
echo "Telegram Advanced Message Forwarder - GitHub Push Tool"
echo "================================================================"
echo "Username: $GITHUB_USERNAME"
echo "Repository: $REPO_NAME"
echo "Branch: $BRANCH"
echo "================================================================"

# Make sure the script is executable
chmod +x push_to_github.sh

# Prepare the repository
echo "✓ Preparing repository..."

# Check for gitignore file
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Sensitive data
.env
*.session
*.session-journal
sessions/

# Logs
logs/
*.log

# Virtual Environment
venv/
ENV/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
EOF
    echo "  → Created .gitignore file"
fi

# Initialize git repository if it doesn't exist
if [ ! -d .git ]; then
    echo "  → Initializing git repository..."
    git init
    # Set default branch name to main
    git branch -M $BRANCH
else
    echo "  → Git repository already initialized"
fi

# Create a clean .git directory without existing history
echo "✓ Preparing files for upload..."

# Ensure that directories exist
mkdir -p sessions
mkdir -p logs
mkdir -p data

# Create a clean README if it doesn't exist
if [ ! -f README.md ]; then
    echo "  → Creating README.md..."
    echo "# Telegram Advanced Message Forwarder" > README.md
fi

# Add all files to git
echo "✓ Adding files to git..."
git add .

# Create a commit
echo "✓ Creating commit..."
git commit -m "Initial commit of Telegram Advanced Message Forwarder"

# Add GitHub remote
echo "✓ Adding GitHub remote..."
if git remote | grep -q "^origin$"; then
    echo "  → Remote 'origin' already exists, updating URL..."
    git remote set-url origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
else
    echo "  → Adding new remote 'origin'..."
    git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
fi

# Push to GitHub
echo "✓ Pushing to GitHub..."
echo "  → You will be prompted for your GitHub username and password/token."
echo "  → Note: If authentication fails, try using a personal access token instead of password."
echo "  → Visit https://github.com/settings/tokens to create a token with 'repo' scope."
echo ""

# Try pushing to GitHub
if git push -u origin $BRANCH; then
    echo ""
    echo "================================================================"
    echo "✅ Success! Your code is now on GitHub!"
    echo "================================================================"
    echo "Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "Next steps:"
    echo "1. Visit the repository URL to verify the upload"
    echo "2. Choose a deployment platform from the deploy/ directory:"
    echo "   - Koyeb: See deploy/koyeb.md"
    echo "   - Heroku: See deploy/heroku.md"
    echo "   - Railway: See deploy/railway.md"
    echo "   - Replit: See deploy/replit.md"
    echo "   - VPS: See deploy/vps.md"
    echo ""
    echo "For help, refer to the README.md file or the deployment guides."
    echo "================================================================"
else
    echo ""
    echo "================================================================"
    echo "❌ Error: Failed to push to GitHub"
    echo "================================================================"
    echo "Possible reasons:"
    echo "1. The repository already exists and is not empty"
    echo "2. Authentication failed"
    echo "3. Network issues"
    echo ""
    echo "Solutions:"
    echo "1. If the repository exists, delete it or use a different name"
    echo "2. Use a personal access token instead of your password"
    echo "   Visit: https://github.com/settings/tokens"
    echo "3. Check your internet connection"
    echo ""
    echo "Try again or manually push your code to GitHub."
    echo "================================================================"
    exit 1
fi