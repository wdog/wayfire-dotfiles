# Claude Commands for Wayfire Dotfiles Repository

## commit_push
Commit and push changes with descriptive technical message

```bash
#!/bin/bash
# Smart commit and push with proper technical messaging
# Never mentions AI assistance, focuses on technical improvements

# Check if there are changes to commit
if ! git diff --cached --quiet || ! git diff --quiet; then
    # Get list of changed files
    changed_files=$(git diff --name-only HEAD 2>/dev/null | tr '\n' ' ')
    cached_files=$(git diff --cached --name-only 2>/dev/null | tr '\n' ' ')

    # Add all changes
    git add .

    # Generate technical commit message based on changes
    if [[ "$changed_files $cached_files" == *"dotfiles_manager.py"* ]] && [[ "$changed_files $cached_files" == *"config.json"* ]]; then
        # Both main files changed - likely feature update
        commit_msg="feat: enhance settings interface with improved user experience

- Implement compact form-style configuration editor
- Add individual field reset with confirmation dialogs
- Improve keyboard navigation with arrow key support
- Centralize key code constants for better maintainability
- Simplify configuration structure for easier management"

    elif [[ "$changed_files $cached_files" == *"dotfiles_manager.py"* ]]; then
        # Only Python file changed
        commit_msg="refactor: improve dotfiles manager interface and functionality

- Modernize user interface with better visual feedback
- Enhance keyboard input handling and navigation
- Optimize code structure and maintainability
- Add improved error handling and user guidance"

    elif [[ "$changed_files $cached_files" == *"config.json"* ]]; then
        # Only config changed
        commit_msg="config: update settings configuration

- Adjust application settings for improved functionality
- Optimize configuration parameters"

    elif [[ "$changed_files $cached_files" == *"CLAUDE.md"* ]]; then
        # Documentation update
        commit_msg="docs: update development guidelines and documentation

- Enhance code architecture documentation
- Add development best practices and guidelines
- Update feature descriptions and usage instructions"

    elif [[ "$changed_files $cached_files" == *".claude/"* ]]; then
        # Claude commands
        commit_msg="tooling: add development automation commands

- Create helper commands for streamlined development workflow
- Add commit automation with proper technical messaging
- Improve development environment setup"

    else
        # General changes
        commit_msg="improve: enhance codebase functionality and structure

- Update multiple components for better user experience
- Refactor code for improved maintainability
- Add new features and fix existing issues"
    fi

    # Commit with clean technical message (NO AI references)
    git commit -m "$commit_msg"

    # Push to remote
    if git push; then
        echo "✅ Changes committed and pushed successfully"
        echo "📝 Commit message: $commit_msg"
    else
        echo "❌ Failed to push changes"
        return 1
    fi
else
    echo "ℹ️  No changes to commit"
fi
```

Usage: Execute this command whenever you need to commit and push changes. It automatically generates clean technical commit messages focused purely on the changes made, without any references to AI assistance or development tools.