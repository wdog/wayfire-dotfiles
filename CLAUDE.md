# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a dotfiles repository for Wayfire Wayland compositor configuration with a Python-based management tool. The repository contains:

- **Wayfire Configuration**: Complete Wayfire compositor setup with plugins, animations, and window management
- **WF-Shell Configuration**: Panel and dock configuration for the Wayfire desktop environment
- **Python Dotfiles Manager**: Rich-based TUI application for managing dotfiles with features like file tracking, settings management, and backup/restore functionality

## Repository Structure

- `.config/wayfire.ini` - Main Wayfire compositor configuration with plugins, keybindings, and visual settings
- `.config/wf-shell.ini` - WF-Shell configuration for panel, dock, and desktop widgets
- `dotfiles_manager.py` - Python TUI application built with Rich library for dotfiles management
- `config.json` - Simplified configuration file for dotfiles manager (git_dir, work_tree, remote only)
- `test_keys.py` - Testing utility for keyboard input functionality
- `venv/` - Python virtual environment with Rich library dependency
- `.gitignore` - Comprehensive ignore patterns for temporary files, caches, and sensitive data

## Common Commands

### Python Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Run the dotfiles manager TUI
python dotfiles_manager.py

# Test keyboard input functionality
python test_keys.py
```

### Configuration Management
- Edit `.config/wayfire.ini` for compositor settings, keybindings, and plugin configuration
- Edit `.config/wf-shell.ini` for panel, dock, and desktop appearance
- Changes take effect after Wayfire restart or reload

## Code Architecture

### Dotfiles Manager (dotfiles_manager.py)
The main application is a Rich-based TUI built around the `DotfilesManager` class:

- **Navigation System**: Cross-platform keyboard input handling using `termios`/`tty` with fallback support
- **Menu Architecture**: Panel-based UI with emoji icons and lime color theme (#32CD32, #9AFF9A, #00FF00, #228B22)
- **Configuration System**: Simplified JSON-based settings (git_dir, work_tree, remote only)
- **Git Integration**: Bare repository management for dotfiles tracking using .gitignore for exclusions
- **Key Components**:
  - `KeyCodes` class: Centralized key code constants with detailed comments for better readability
  - `get_key()`: Universal keyboard input function for arrow key navigation with ANSI escape sequence handling
  - `handle_menu_navigation()`: Processes keyboard input and menu selection with arrow keys and WASD/HJKL
  - `display_menu()`: Renders the main interface using Rich panels and styling
  - `load_config()`/`save_config()`: Simplified configuration management (removed file filtering)
  - `settings()`: Settings submenu with form-style editor and git initialization
  - `edit_settings()`: **Compact form-style interface** for real-time editing of all configurations
  - `file_browser()`: Multi-column file browser with arrow navigation and search functionality
  - `initialize_git_repo()`: Automated bare git repository setup

### Wayfire Configuration Architecture

The Wayfire configuration is organized into plugin sections:

- **Core plugins**: window management (simple-tile), workspace switching (vswitch), animations (animate)
- **Visual effects**: blur, decoration, wobbly windows, shadows
- **Input handling**: gesture controls, keyboard shortcuts, mouse actions
- **Applications**: autostart programs, command bindings
- **Advanced features**: cube workspace switcher, expo view, scale overview

Key plugins enabled:
- `simple-tile` - Automatic window tiling with configurable gaps
- `animate` - Window animations (zoom, fire effects)
- `decoration` - Window borders and titlebar styling
- `blur` - Background blur effects using kawase method
- `vswitch` - Virtual workspace management (4x2 grid)

### WF-Shell Configuration
Desktop shell components:

- **Panel**: Top bar with widgets (menu, launchers, window-list, clock, tray)
- **Dock**: Bottom auto-hiding dock for frequently used applications
- **Background**: Wallpaper management with fade transitions

## Key Configuration Areas

- **Keybindings**: Defined in `[command]` and plugin-specific sections of wayfire.ini
- **Visual styling**: Colors, fonts, and effects in `[decoration]`, `[blur]`, etc.
- **Window behavior**: Rules and defaults in `[window-rules]`, `[place]`, `[simple-tile]`
- **Workspace layout**: Grid configuration in `[core]` (vwidth/vheight = 4x2)

## Dotfiles Manager Features

### Configuration System
- **JSON Configuration**: `config.json` simplified to core settings only (removed file filtering)
- **Git Settings**: `git_dir` (default: ~/.dotfiles.git), `work_tree` (default: ~), `remote`
- **File Management**: Uses repository .gitignore for exclusion patterns instead of internal filtering
- **Settings Interface**: **Compact form-style editor** with real-time field editing and individual field reset

### Settings Menu (`dotfiles_manager.py:settings()`)
1. **✏️ Modifica Settings** - Compact form-style editor for all configuration options
2. **🚀 Inizializza Repo Git** - Automated bare repository setup with work tree
3. **🔙 Torna al Menu** - Return to main menu

### Form-Style Settings Editor (`dotfiles_manager.py:edit_settings()`)
**Modern compact interface design:**
- **All fields visible simultaneously**: 3 settings in single compact view
- **Real-time visual feedback**: Active field highlighted, inactive fields dimmed
- **Inline editing mode**: Direct field editing with cursor indicator (█)
- **Individual field reset**: Reset only current field to default with elegant confirmation dialog

**Navigation & Controls:**
- `↑↓`: Navigate between fields (Arrow Keys)
- `Enter`: Start/confirm editing current field
- `Esc`: Cancel current edit
- `Backspace`: Remove characters during editing
- `s`: Save all changes
- `r`: Reset **current field only** to default value
- `q`: Exit without saving

**Visual States:**
- **Inactive field**: Dimmed gray appearance
- **Active field**: Lime green highlighting (►)
- **Editing field**: Green background with cursor (✏️)
- **Placeholders**: Show default values when empty

**Reset Confirmation Dialog:**
- Shows current vs default values
- Elegant panel with field details
- Confirmation required (s/n)

### Git Integration
- **Bare Repository**: Automated initialization with `initialize_git_repo()`
- **Work Tree Configuration**: Proper setup for dotfiles tracking
- **Remote Support**: Optional remote repository configuration
- **Alias Generation**: Provides commands for dotfiles management

### Key Functions
- `load_config()`: Simplified configuration loading (core settings only)
- `save_config()`: JSON configuration persistence
- `edit_settings()`: **Compact form-style settings editor with real-time editing**
- `initialize_git_repo()`: Bare repository initialization
- `get_key()`: Cross-platform keyboard input with ANSI escape sequence handling

### KeyCodes Class (`dotfiles_manager.py:KeyCodes`)
**Centralized key code constants for better code readability:**
- **Control keys**: ESC (\x1b), ENTER (\r), CTRL_C (\x03)
- **Backspace variants**: BACKSPACE (\x7f), BACKSPACE_ALT (\x08) for different terminals
- **Arrow keys**: ARROW_UP (\x1b[A), ARROW_DOWN (\x1b[B), ARROW_LEFT (\x1b[D), ARROW_RIGHT (\x1b[C)
- **Function keys**: F1-F4 (\x1bOP-\x1bOS)
- **Special keys**: HOME, END, PAGE_UP, PAGE_DOWN, DELETE

**Usage throughout codebase:** All key handling uses `KeyCodes.CONSTANT_NAME` instead of raw escape sequences for better maintainability and readability.

## Development Notes

This is primarily a configuration repository with a Python TUI tool. No build system or tests are required for the configuration files. The Python application uses:

- **Rich library** for terminal UI components with lime color theme
- **Cross-platform keyboard input** handling with KeyCodes constants
- **Compact form-based interfaces** for modern UX design
- **Simplified configuration system** using only .gitignore for file exclusions
- **Real-time editing capabilities** with visual feedback
- **Elegant confirmation dialogs** for destructive operations
- **JSON-based configuration** (core settings only: git_dir, work_tree, remote)
- **Subprocess integration** for Git operations

## Development Guidelines

### Code Style & Architecture
- **Use KeyCodes constants** instead of raw escape sequences for all key handling
- **Prefer compact form interfaces** over menu-driven navigation where possible
- **Implement real-time visual feedback** for active elements (highlighting, cursors, etc.)
- **Use repository .gitignore** for file exclusions instead of internal filtering
- **Keep configuration minimal** - avoid feature creep in settings
- **Provide elegant confirmation dialogs** for destructive operations (resets, deletions)

### UI/UX Principles
- **All related settings visible simultaneously** in compact forms
- **Clear visual states** for inactive/active/editing modes
- **Individual field operations** rather than bulk operations where practical
- **Consistent lime color theme** throughout the interface (#32CD32, #9AFF9A, etc.)
- **Keyboard-first navigation** with arrow keys and vim-style alternatives (hjkl)
- **Immediate feedback** for user actions with status messages

### File Management
- **Rely on .gitignore** for exclusion patterns instead of internal filtering
- **Simplified config.json** with only essential settings (git_dir, work_tree, remote)
- **No internal file pattern matching** - let git handle what should be tracked

Configuration follows INI format with section-based organization. Comments use semicolon (;) prefix.

## Important Directives
- **NEVER mention "Claude" in commit messages** - use descriptive technical language only
- Always use KeyCodes constants for key handling
- Prefer form-style interfaces over traditional menus
- Individual field reset rather than bulk reset operations
- Use .gitignore for file exclusions, not internal filtering

## ⚠️ CRITICAL - Commit Guidelines
- **ABSOLUTELY NEVER mention Claude, AI assistance, or any similar terms in commits**
- **Commits MUST appear as if written by a human developer**
- **NO references to "Generated with", "Co-Authored-By Claude", etc.**
- **FOCUS ONLY on technical changes and improvements**

### Commit Format
- Use conventional commit format: `type(scope): description`
- Focus on **what changed** and **why** it's beneficial
- Examples of good commits:
  - `feat: add compact form-style settings editor`
  - `refactor: centralize key codes with constants class`
  - `improve: replace bulk reset with individual field reset`
- **Avoid**: Any reference to AI assistance, Claude, or similar terms
- **Focus**: Technical improvements, user experience enhancements, code quality

### VIOLATION CONSEQUENCES
- Any commit with Claude/AI references must be IMMEDIATELY corrected
- Use `git commit --amend` or `git rebase -i` to fix commit messages
- Force push may be required to clean repository history

## Future Development Roadmap

### XDG Base Directory Migration Plan
The application currently uses a simple local config approach for ease of development. Future migration to XDG compliance:

#### Phase 1: Hybrid Approach (Current)
- **Config**: `config.json` in application directory (simple, portable)
- **Gitignore**: `~/.config/dotfiles-manager/.gitignore` (XDG compliant, system clean)
- **Benefits**: Maintains simplicity while organizing system-level files properly

#### Phase 2: Full XDG Migration (Future)
- **Config directory**: `~/.config/dotfiles-manager/`
- **Config file**: `~/.config/dotfiles-manager/config.json`
- **Data directory**: `~/.local/share/dotfiles-manager/` (for backups, templates)
- **Cache directory**: `~/.cache/dotfiles-manager/` (for temporary files)

#### Migration Strategy
- **Backward compatibility**: Check both old and new locations
- **Auto-migration**: Move config.json from app dir to XDG location on first run
- **User notification**: Inform about new configuration location
- **Graceful fallback**: If XDG directories unavailable, use local config

#### Implementation Considerations
- Use `os.environ.get('XDG_CONFIG_HOME', '~/.config')` for portability
- Create directories only when needed
- Maintain single-file portability option for development/testing
- Update documentation with new file locations
