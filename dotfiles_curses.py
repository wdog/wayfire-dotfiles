#!/usr/bin/env python3

import os
import sys
import subprocess
import curses
import shutil
from pathlib import Path
import difflib
from datetime import datetime
from typing import List, Tuple, Optional
from config_manager import ConfigManager

class CursesDotfilesManager:
    def __init__(self):
        self.repo_path = Path(__file__).parent.absolute()
        self.home_path = Path.home()
        self.stdscr = None
        self.config = ConfigManager(self.repo_path)
        
    def run_git_command(self, args):
        """Run a git command in the repo directory"""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return None
    
    def setup_colors(self):
        """Initialize color pairs for curses"""
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Selected
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Added/Success
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Removed/Error
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Modified/Warning
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
            curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Special
    
    def draw_border(self, win, title=""):
        """Draw a border around a window with optional title"""
        win.box()
        if title:
            win.addstr(0, 2, f" {title} ", curses.color_pair(1) | curses.A_BOLD)
    
    def show_status(self, message, color_pair=0, delay=1.5):
        """Show status message at bottom of screen"""
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height-1, 0, " " * width)
        self.stdscr.addstr(height-1, 2, message[:width-4], color_pair)
        self.stdscr.refresh()
        if delay > 0:
            curses.napms(int(delay * 1000))
    
    def get_config_files(self, pattern=""):
        """Get list of config files using configuration"""
        return self.config.get_config_files(pattern)
    
    def input_dialog(self, title, prompt, default=""):
        """Show input dialog and return user input"""
        height, width = self.stdscr.getmaxyx()
        dialog_height = 7
        dialog_width = min(60, width - 4)
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        dialog = curses.newwin(dialog_height, dialog_width, start_y, start_x)
        self.draw_border(dialog, title)
        
        dialog.addstr(2, 2, prompt)
        dialog.addstr(4, 2, default)
        dialog.refresh()
        
        # Enable cursor and text input
        curses.curs_set(1)
        input_win = curses.newwin(1, dialog_width - 6, start_y + 4, start_x + 2)
        input_win.addstr(0, 0, default)
        input_win.refresh()
        
        result = ""
        pos = len(default)
        
        while True:
            key = input_win.getch()
            
            if key == ord('\n') or key == 10:  # Enter
                break
            elif key == 27:  # Escape
                result = None
                break
            elif key == curses.KEY_BACKSPACE or key == 127:
                if pos > 0:
                    pos -= 1
                    result = result[:pos] + result[pos+1:]
                    input_win.clear()
                    input_win.addstr(0, 0, result)
                    input_win.move(0, pos)
            elif 32 <= key <= 126:  # Printable characters
                result = result[:pos] + chr(key) + result[pos:]
                pos += 1
                input_win.clear()
                input_win.addstr(0, 0, result)
                input_win.move(0, pos)
            
            input_win.refresh()
        
        curses.curs_set(0)
        dialog.clear()
        dialog.refresh()
        
        return result if result is not None else default
    
    def multi_select_files(self):
        """Curses-based multi-select file browser"""
        files = self.get_config_files()
        if not files:
            self.show_status("No configuration files found!", curses.color_pair(4))
            return []
        
        selected = set()
        current = 0
        scroll_offset = 0
        
        height, width = self.stdscr.getmaxyx()
        list_height = height - 6
        
        while True:
            self.stdscr.clear()
            
            # Header
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "📁 Add Files to Repository", curses.color_pair(1) | curses.A_BOLD)
            
            # Instructions
            self.stdscr.addstr(2, 2, "Use ↑↓ to navigate, SPACE to select/deselect, ENTER to confirm, ESC to cancel", curses.color_pair(6))
            
            # File list
            for i in range(list_height):
                file_idx = scroll_offset + i
                if file_idx >= len(files):
                    break
                
                file_path = files[file_idx]
                repo_file = self.repo_path / file_path
                
                # Status indicators
                if repo_file.exists():
                    status_icon = "✅"
                    status_color = curses.color_pair(3)
                else:
                    status_icon = "➕"
                    status_color = curses.color_pair(5)
                
                # Selection indicator
                select_icon = "☑️ " if file_idx in selected else "☐ "
                
                # Current item highlighting
                if file_idx == current:
                    attr = curses.color_pair(2) | curses.A_BOLD
                else:
                    attr = curses.color_pair(0)
                
                line = f"{select_icon}{status_icon} {file_path}"
                line = line[:width-4]
                
                self.stdscr.addstr(4 + i, 2, " " * (width-4), attr)
                self.stdscr.addstr(4 + i, 2, line, attr)
            
            # Status bar
            status = f"Selected: {len(selected)} | Total: {len(files)}"
            self.stdscr.addstr(height-2, 2, status, curses.color_pair(6))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                if current > 0:
                    current -= 1
                    if current < scroll_offset:
                        scroll_offset = current
            elif key == curses.KEY_DOWN:
                if current < len(files) - 1:
                    current += 1
                    if current >= scroll_offset + list_height:
                        scroll_offset = current - list_height + 1
            elif key == ord(' '):  # Space to toggle selection
                if current in selected:
                    selected.remove(current)
                else:
                    selected.add(current)
            elif key == ord('a') or key == ord('A'):  # Select all
                selected = set(range(len(files)))
            elif key == ord('n') or key == ord('N'):  # Select none
                selected.clear()
            elif key == ord('\n') or key == 10:  # Enter to confirm
                return [files[i] for i in sorted(selected)]
            elif key == 27:  # Escape to cancel
                return []
    
    def show_diff_viewer(self, file_path=None):
        """Curses-based diff viewer"""
        # Get files to check
        if file_path:
            files_to_check = [file_path]
        else:
            tracked_files = self.run_git_command(['ls-files'])
            if not tracked_files:
                self.show_status("No tracked files found!", curses.color_pair(4))
                return
            files_to_check = tracked_files.split('\n')
        
        # Collect all diffs
        all_diffs = []
        for file_rel_path in files_to_check:
            repo_file = self.repo_path / file_rel_path
            home_file = self.home_path / file_rel_path
            
            if not repo_file.exists() or not home_file.exists():
                continue
            
            try:
                with open(repo_file, 'r') as f:
                    repo_content = f.readlines()
                with open(home_file, 'r') as f:
                    home_content = f.readlines()
                
                diff = list(difflib.unified_diff(
                    repo_content,
                    home_content,
                    fromfile=f"repo/{file_rel_path}",
                    tofile=f"home/{file_rel_path}",
                    lineterm=""
                ))
                
                if diff:
                    all_diffs.extend([f"📄 {file_rel_path}"] + diff + [""])
                else:
                    all_diffs.append(f"✅ {file_rel_path}: No differences")
            
            except Exception as e:
                all_diffs.append(f"❌ Error comparing {file_rel_path}: {e}")
        
        if not all_diffs:
            self.show_status("No differences found!", curses.color_pair(3))
            return
        
        # Show diff viewer
        scroll_offset = 0
        height, width = self.stdscr.getmaxyx()
        content_height = height - 4
        
        while True:
            self.stdscr.clear()
            
            # Header
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "🔍 File Differences", curses.color_pair(1) | curses.A_BOLD)
            
            # Instructions
            self.stdscr.addstr(1, 2, "Use ↑↓/PgUp/PgDn to scroll, ESC to return", curses.color_pair(6))
            
            # Content
            for i in range(content_height):
                line_idx = scroll_offset + i
                if line_idx >= len(all_diffs):
                    break
                
                line = all_diffs[line_idx][:width-4]
                
                # Color coding
                if line.startswith('+++') or line.startswith('---'):
                    color = curses.color_pair(6)
                elif line.startswith('@@'):
                    color = curses.color_pair(7)
                elif line.startswith('+'):
                    color = curses.color_pair(3)
                elif line.startswith('-'):
                    color = curses.color_pair(4)
                elif line.startswith('📄'):
                    color = curses.color_pair(1) | curses.A_BOLD
                elif line.startswith('✅'):
                    color = curses.color_pair(3)
                else:
                    color = curses.color_pair(0)
                
                self.stdscr.addstr(2 + i, 2, line, color)
            
            # Scroll indicators
            if scroll_offset > 0:
                self.stdscr.addstr(2, width-3, "↑", curses.color_pair(6))
            if scroll_offset + content_height < len(all_diffs):
                self.stdscr.addstr(height-3, width-3, "↓", curses.color_pair(6))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                if scroll_offset > 0:
                    scroll_offset -= 1
            elif key == curses.KEY_DOWN:
                if scroll_offset + content_height < len(all_diffs):
                    scroll_offset += 1
            elif key == curses.KEY_PPAGE:  # Page Up
                scroll_offset = max(0, scroll_offset - content_height)
            elif key == curses.KEY_NPAGE:  # Page Down
                scroll_offset = min(len(all_diffs) - content_height, scroll_offset + content_height)
            elif key == 27:  # Escape
                break
    
    def commit_and_push_dialog(self):
        """Curses-based commit and push interface"""
        # Check for changes
        status = self.run_git_command(['status', '--porcelain'])
        if not status:
            self.show_status("No changes to commit!", curses.color_pair(5))
            return
        
        height, width = self.stdscr.getmaxyx()
        
        # Show changes
        changes = status.split('\n')
        
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
        self.stdscr.addstr(0, 2, "💾 Commit Changes", curses.color_pair(1) | curses.A_BOLD)
        
        self.stdscr.addstr(2, 2, "Current changes:", curses.color_pair(6))
        for i, change in enumerate(changes[:height-8]):
            status_code = change[:2]
            filename = change[3:] if len(change) > 3 else ""
            
            if 'M' in status_code:
                color = curses.color_pair(5)  # Modified
            elif 'A' in status_code:
                color = curses.color_pair(3)  # Added
            elif 'D' in status_code:
                color = curses.color_pair(4)  # Deleted
            else:
                color = curses.color_pair(0)
            
            self.stdscr.addstr(4 + i, 4, f"{status_code} {filename}", color)
        
        self.stdscr.refresh()
        
        # Get commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = self.config.get_commit_message_template()
        default_message = template.format(timestamp=timestamp)
        
        message = self.input_dialog("Commit Message", "Enter commit message:", default_message)
        
        if not message:
            self.show_status("Commit cancelled", curses.color_pair(5))
            return
        
        # Commit
        self.show_status("Committing changes...", curses.color_pair(6), 0)
        result = self.run_git_command(['commit', '-m', message])
        if result is None:
            self.show_status("Commit failed!", curses.color_pair(4))
            return
        
        self.show_status("Committed successfully! Pushing...", curses.color_pair(3), 0)
        
        # Push
        result = self.run_git_command(['push'])
        if result is None:
            self.show_status("Push failed!", curses.color_pair(4))
            return
        
        self.show_status("Successfully committed and pushed!", curses.color_pair(3))
    
    def restore_file_dialog(self):
        """Curses-based file restoration interface"""
        # Get tracked files
        tracked_files = self.run_git_command(['ls-files'])
        if not tracked_files:
            self.show_status("No tracked files found!", curses.color_pair(4))
            return
        
        files = tracked_files.split('\n')
        current = 0
        
        height, width = self.stdscr.getmaxyx()
        list_height = height - 6
        
        # File selection
        while True:
            self.stdscr.clear()
            
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "🔄 Restore File from History", curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(2, 2, "Select file to restore (↑↓ to navigate, ENTER to select, ESC to cancel):", curses.color_pair(6))
            
            for i in range(min(list_height, len(files))):
                if i >= len(files):
                    break
                
                attr = curses.color_pair(2) | curses.A_BOLD if i == current else curses.color_pair(0)
                line = f"{i+1:3d}. {files[i]}"[:width-6]
                
                self.stdscr.addstr(4 + i, 2, " " * (width-4), attr)
                self.stdscr.addstr(4 + i, 2, line, attr)
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(files) - 1:
                current += 1
            elif key == ord('\n') or key == 10:  # Enter
                selected_file = files[current]
                break
            elif key == 27:  # Escape
                return
        
        # Get commit history
        log_result = self.run_git_command([
            'log', '--oneline', '--follow', '-n', '10', '--', selected_file
        ])
        
        if not log_result:
            self.show_status(f"No history found for {selected_file}!", curses.color_pair(4))
            return
        
        commits = log_result.split('\n')
        current = 0
        
        # Commit selection
        while True:
            self.stdscr.clear()
            
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, f"📅 History: {selected_file}", curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(2, 2, "Select commit to restore from:", curses.color_pair(6))
            
            for i, commit in enumerate(commits):
                attr = curses.color_pair(2) | curses.A_BOLD if i == current else curses.color_pair(0)
                line = f"{i+1:3d}. {commit}"[:width-6]
                
                self.stdscr.addstr(4 + i, 2, " " * (width-4), attr)
                self.stdscr.addstr(4 + i, 2, line, attr)
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(commits) - 1:
                current += 1
            elif key == ord('\n') or key == 10:  # Enter
                commit_hash = commits[current].split()[0]
                
                # Restore file
                self.show_status(f"Restoring {selected_file} from {commit_hash}...", curses.color_pair(6), 0)
                
                result = self.run_git_command(['checkout', commit_hash, '--', selected_file])
                if result is None:
                    self.show_status("Restoration failed!", curses.color_pair(4))
                    return
                
                # Copy to home directory
                repo_file = self.repo_path / selected_file
                home_file = self.home_path / selected_file
                
                if repo_file.exists():
                    home_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(repo_file, home_file)
                    
                    # Stage the change
                    self.run_git_command(['add', selected_file])
                    
                    self.show_status(f"Successfully restored {selected_file}! File staged for commit.", curses.color_pair(3))
                else:
                    self.show_status(f"Failed to restore {selected_file}!", curses.color_pair(4))
                return
            elif key == 27:  # Escape
                return
    
    def add_files_interface(self):
        """Add files interface"""
        selected_files = self.multi_select_files()
        
        if not selected_files:
            self.show_status("No files selected", curses.color_pair(5))
            return
        
        self.show_status(f"Adding {len(selected_files)} files...", curses.color_pair(6), 0)
        
        added_files = []
        for file_path in selected_files:
            source = self.home_path / file_path
            dest = self.repo_path / file_path
            
            if not source.exists():
                continue
            
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                self.run_git_command(['add', str(file_path)])
                added_files.append(file_path)
            except Exception:
                continue
        
        if added_files:
            self.show_status(f"Successfully added {len(added_files)} files! Use commit to save changes.", curses.color_pair(3))
        else:
            self.show_status("No files were added", curses.color_pair(4))
    
    def config_menu(self):
        """Configuration management menu"""
        menu_items = [
            ("📂 Search Paths", "Manage directories to search for config files"),
            ("🚫 Gitignore Patterns", "Manage patterns to exclude from repository"),
            ("📄 File Patterns", "Manage file patterns to include"),
            ("⚙️  General Settings", "Edit general configuration settings"),
            ("📤 Export Config", "Export configuration to file"),
            ("📥 Import Config", "Import configuration from file"),
            ("🔄 Reset Defaults", "Reset configuration to defaults"),
            ("🔙 Back", "Return to main menu")
        ]
        
        current = 0
        
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Header
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "⚙️  Configuration", curses.color_pair(1) | curses.A_BOLD)
            
            # Menu items
            for i, (title, desc) in enumerate(menu_items):
                if i == current:
                    attr = curses.color_pair(2) | curses.A_BOLD
                    self.stdscr.addstr(3 + i * 2, 2, " " * (width - 4), attr)
                    self.stdscr.addstr(3 + i * 2, 4, title, attr)
                    self.stdscr.addstr(4 + i * 2, 6, desc, curses.color_pair(6))
                else:
                    self.stdscr.addstr(3 + i * 2, 4, title, curses.color_pair(0))
                    self.stdscr.addstr(4 + i * 2, 6, desc, curses.color_pair(6))
            
            # Instructions
            self.stdscr.addstr(height - 2, 2, "Use ↑↓ to navigate, ENTER to select, ESC to back", curses.color_pair(6))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                current = (current - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                current = (current + 1) % len(menu_items)
            elif key == ord('\n') or key == 10:  # Enter
                if current == 0:  # Search Paths
                    self.manage_search_paths()
                elif current == 1:  # Gitignore Patterns
                    self.manage_gitignore_patterns()
                elif current == 2:  # File Patterns
                    self.manage_file_patterns()
                elif current == 3:  # General Settings
                    self.show_status("General settings editor not implemented yet", curses.color_pair(5))
                elif current == 4:  # Export Config
                    self.export_config()
                elif current == 5:  # Import Config
                    self.import_config()
                elif current == 6:  # Reset Defaults
                    if self.confirm_dialog("Reset Configuration", "Are you sure you want to reset to defaults?"):
                        self.config.reset_to_defaults()
                        self.show_status("Configuration reset to defaults", curses.color_pair(3))
                elif current == 7:  # Back
                    break
            elif key == 27:  # Escape
                break
    
    def manage_search_paths(self):
        """Manage search paths interface"""
        while True:
            paths = self.config.config["search_paths"]
            
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "📂 Search Paths", curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(2, 2, "Current search paths:", curses.color_pair(6))
            
            for i, path in enumerate(paths):
                color = curses.color_pair(3) if Path(path).expanduser().exists() else curses.color_pair(4)
                self.stdscr.addstr(4 + i, 4, f"{i+1}. {path}", color)
            
            self.stdscr.addstr(height - 4, 2, "Commands: [A]dd, [R]emove, [ESC] Back", curses.color_pair(6))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == ord('a') or key == ord('A'):
                new_path = self.input_dialog("Add Search Path", "Enter new search path:")
                if new_path:
                    self.config.add_search_path(new_path)
                    self.show_status(f"Added search path: {new_path}", curses.color_pair(3))
            elif key == ord('r') or key == ord('R'):
                if paths:
                    idx_str = self.input_dialog("Remove Path", f"Enter number (1-{len(paths)}):")
                    try:
                        idx = int(idx_str) - 1
                        if 0 <= idx < len(paths):
                            removed_path = paths[idx]
                            self.config.remove_search_path(removed_path)
                            self.show_status(f"Removed search path: {removed_path}", curses.color_pair(3))
                    except ValueError:
                        self.show_status("Invalid number", curses.color_pair(4))
            elif key == 27:  # Escape
                break
    
    def manage_gitignore_patterns(self):
        """Manage gitignore patterns interface"""
        scroll_offset = 0
        
        while True:
            patterns = self.config.config["gitignore_patterns"]
            
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            content_height = height - 6
            
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "🚫 Gitignore Patterns", curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(2, 2, f"Current patterns ({len(patterns)} total):", curses.color_pair(6))
            
            for i in range(min(content_height, len(patterns) - scroll_offset)):
                pattern_idx = scroll_offset + i
                if pattern_idx < len(patterns):
                    pattern = patterns[pattern_idx]
                    line = f"{pattern_idx+1:3d}. {pattern}"[:width-6]
                    self.stdscr.addstr(4 + i, 4, line, curses.color_pair(0))
            
            # Scroll indicators
            if scroll_offset > 0:
                self.stdscr.addstr(4, width-3, "↑", curses.color_pair(6))
            if scroll_offset + content_height < len(patterns):
                self.stdscr.addstr(height-3, width-3, "↓", curses.color_pair(6))
            
            self.stdscr.addstr(height - 4, 2, "Commands: [A]dd, [R]emove, [↑↓] Scroll, [ESC] Back", curses.color_pair(6))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP and scroll_offset > 0:
                scroll_offset -= 1
            elif key == curses.KEY_DOWN and scroll_offset + content_height < len(patterns):
                scroll_offset += 1
            elif key == ord('a') or key == ord('A'):
                new_pattern = self.input_dialog("Add Gitignore Pattern", "Enter pattern (e.g., *.log):")
                if new_pattern:
                    self.config.add_gitignore_pattern(new_pattern)
                    self.show_status(f"Added gitignore pattern: {new_pattern}", curses.color_pair(3))
            elif key == ord('r') or key == ord('R'):
                if patterns:
                    idx_str = self.input_dialog("Remove Pattern", f"Enter number (1-{len(patterns)}):")
                    try:
                        idx = int(idx_str) - 1
                        if 0 <= idx < len(patterns):
                            removed_pattern = patterns[idx]
                            self.config.remove_gitignore_pattern(removed_pattern)
                            self.show_status(f"Removed pattern: {removed_pattern}", curses.color_pair(3))
                    except ValueError:
                        self.show_status("Invalid number", curses.color_pair(4))
            elif key == 27:  # Escape
                break
    
    def manage_file_patterns(self):
        """Manage file patterns interface"""
        while True:
            patterns = self.config.config["file_patterns"]
            
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "📄 File Patterns", curses.color_pair(1) | curses.A_BOLD)
            
            self.stdscr.addstr(2, 2, "File patterns to include:", curses.color_pair(6))
            
            for i, pattern in enumerate(patterns):
                self.stdscr.addstr(4 + i, 4, f"{i+1}. {pattern}", curses.color_pair(0))
            
            self.stdscr.addstr(height - 4, 2, "Commands: [A]dd, [R]emove, [ESC] Back", curses.color_pair(6))
            
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == ord('a') or key == ord('A'):
                new_pattern = self.input_dialog("Add File Pattern", "Enter pattern (e.g., *.conf):")
                if new_pattern:
                    self.config.add_file_pattern(new_pattern)
                    self.show_status(f"Added file pattern: {new_pattern}", curses.color_pair(3))
            elif key == ord('r') or key == ord('R'):
                if patterns:
                    idx_str = self.input_dialog("Remove Pattern", f"Enter number (1-{len(patterns)}):")
                    try:
                        idx = int(idx_str) - 1
                        if 0 <= idx < len(patterns):
                            removed_pattern = patterns[idx]
                            self.config.remove_file_pattern(removed_pattern)
                            self.show_status(f"Removed pattern: {removed_pattern}", curses.color_pair(3))
                    except ValueError:
                        self.show_status("Invalid number", curses.color_pair(4))
            elif key == 27:  # Escape
                break
    
    def confirm_dialog(self, title, message):
        """Show confirmation dialog"""
        height, width = self.stdscr.getmaxyx()
        dialog_height = 7
        dialog_width = min(50, width - 4)
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        dialog = curses.newwin(dialog_height, dialog_width, start_y, start_x)
        self.draw_border(dialog, title)
        
        dialog.addstr(2, 2, message[:dialog_width-4])
        dialog.addstr(4, 2, "Press Y to confirm, N to cancel")
        dialog.refresh()
        
        while True:
            key = dialog.getch()
            if key == ord('y') or key == ord('Y'):
                dialog.clear()
                dialog.refresh()
                return True
            elif key == ord('n') or key == ord('N') or key == 27:
                dialog.clear()
                dialog.refresh()
                return False
    
    def export_config(self):
        """Export configuration to file"""
        filename = self.input_dialog("Export Config", "Enter filename:", "dotfiles_config.json")
        if filename:
            try:
                export_path = Path(filename)
                if not export_path.is_absolute():
                    export_path = self.repo_path / filename
                self.config.export_config(export_path)
                self.show_status(f"Configuration exported to {export_path}", curses.color_pair(3))
            except Exception as e:
                self.show_status(f"Export failed: {e}", curses.color_pair(4))
    
    def import_config(self):
        """Import configuration from file"""
        filename = self.input_dialog("Import Config", "Enter filename:", "dotfiles_config.json")
        if filename:
            try:
                import_path = Path(filename)
                if not import_path.is_absolute():
                    import_path = self.repo_path / filename
                
                if not import_path.exists():
                    self.show_status(f"File not found: {import_path}", curses.color_pair(4))
                    return
                
                if self.config.import_config(import_path):
                    self.show_status(f"Configuration imported from {import_path}", curses.color_pair(3))
                else:
                    self.show_status("Import failed", curses.color_pair(4))
            except Exception as e:
                self.show_status(f"Import failed: {e}", curses.color_pair(4))
    
    def main_menu(self):
        """Main menu interface"""
        menu_items = [
            ("📁 Add Files", "Add configuration files to repository"),
            ("🔍 View Diff", "Compare repository and filesystem files"),
            ("💾 Commit & Push", "Commit changes and push to remote"),
            ("🔄 Restore File", "Restore file from git history"),
            ("⚙️  Configuration", "Manage dotfiles configuration"),
            ("❌ Exit", "Exit the application")
        ]
        
        current = 0
        
        while True:
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Header
            self.stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
            self.stdscr.addstr(0, 2, "🛠️  Dotfiles Manager", curses.color_pair(1) | curses.A_BOLD)
            
            # Repository info
            repo_name = self.repo_path.name
            self.stdscr.addstr(2, 2, f"Repository: {repo_name}", curses.color_pair(6))
            
            # Menu items
            for i, (title, desc) in enumerate(menu_items):
                if i == current:
                    attr = curses.color_pair(2) | curses.A_BOLD
                    self.stdscr.addstr(4 + i * 2, 2, " " * (width - 4), attr)
                    self.stdscr.addstr(4 + i * 2, 4, title, attr)
                    self.stdscr.addstr(5 + i * 2, 6, desc, curses.color_pair(6))
                else:
                    self.stdscr.addstr(4 + i * 2, 4, title, curses.color_pair(0))
                    self.stdscr.addstr(5 + i * 2, 6, desc, curses.color_pair(6))
            
            # Instructions
            self.stdscr.addstr(height - 3, 2, "Use ↑↓ to navigate, ENTER to select, Q to quit", curses.color_pair(6))
            
            # Git status
            status = self.run_git_command(['status', '--porcelain'])
            if status:
                changes = len(status.split('\n'))
                self.stdscr.addstr(height - 2, 2, f"⚠️  {changes} uncommitted changes", curses.color_pair(5))
            else:
                self.stdscr.addstr(height - 2, 2, "✅ No uncommitted changes", curses.color_pair(3))
            
            self.stdscr.refresh()
            
            # Handle input
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP:
                current = (current - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                current = (current + 1) % len(menu_items)
            elif key == ord('\n') or key == 10:  # Enter
                if current == 0:  # Add Files
                    self.add_files_interface()
                elif current == 1:  # View Diff
                    self.show_diff_viewer()
                elif current == 2:  # Commit & Push
                    self.commit_and_push_dialog()
                elif current == 3:  # Restore File
                    self.restore_file_dialog()
                elif current == 4:  # Configuration
                    self.config_menu()
                elif current == 5:  # Exit
                    break
            elif key == ord('q') or key == ord('Q') or key == 27:  # Quit
                break
    
    def run(self):
        """Main application runner"""
        def main_wrapper(stdscr):
            self.stdscr = stdscr
            curses.curs_set(0)  # Hide cursor
            self.setup_colors()
            self.main_menu()
        
        curses.wrapper(main_wrapper)

if __name__ == "__main__":
    manager = CursesDotfilesManager()
    try:
        manager.run()
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)