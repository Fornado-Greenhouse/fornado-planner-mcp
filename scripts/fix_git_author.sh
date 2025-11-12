#!/bin/bash

# Script to fix git author information in commit history
# This will change all commits from the Replit user to your GitHub user

echo "========================================"
echo "Git Author History Rewrite Script"
echo "========================================"
echo ""
echo "This script will rewrite git history to change the author from:"
echo "  mrfranklucasusa <37761362-mrfranklucasusa@users.noreply.replit.com>"
echo "to:"
echo "  alexfoley <alexfoley@gmail.com>"
echo ""
echo "WARNING: This will rewrite git history!"
echo "Make sure you have a backup of your repository."
echo ""
read -p "Do you want to proceed? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Rewriting git history..."
    
    git filter-branch -f --env-filter '
    OLD_EMAIL="37761362-mrfranklucasusa@users.noreply.replit.com"
    CORRECT_NAME="alexfoley"
    CORRECT_EMAIL="alexfoley@gmail.com"
    
    if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
    then
        export GIT_COMMITTER_NAME="$CORRECT_NAME"
        export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
    fi
    if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
    then
        export GIT_AUTHOR_NAME="$CORRECT_NAME"
        export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
    fi
    ' --tag-name-filter cat -- --branches --tags
    
    echo ""
    echo "✅ Git history has been rewritten!"
    echo ""
    echo "To verify the changes, run:"
    echo "  git log --pretty=format:'%h - %an <%ae> : %s' -5"
    echo ""
    echo "IMPORTANT: Since history was rewritten, you'll need to force push:"
    echo "  git push --force origin main"
    echo ""
    echo "⚠️  WARNING: Force pushing will overwrite the remote history."
    echo "Make sure no one else is working on this repository!"
else
    echo "Operation cancelled."
fi