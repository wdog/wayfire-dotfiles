#!/usr/bin/env python3
"""
Wayfire Dotfiles Manager
A beautiful TUI tool for managing dotfiles with Rich library
"""

import os
import sys
import termios
import tty
import json
import glob
import fnmatch
import subprocess
import shutil
from pathlib import Path
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.table import Table
from rich.columns import Columns
from rich import box
from rich.padding import Padding

# Create console with lime theme
console = Console()

def get_key():
    """Cross-platform single key input function with fallback"""
    try:
        if os.name == 'nt':  # Windows
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:  # Unix/Linux/MacOS
            # Check if stdin is a terminal
            if not sys.stdin.isatty():
                # Fallback to regular input for non-interactive environments
                return input().strip() or '\r'

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                if key == '\x1b':  # Arrow keys start with escape
                    key += sys.stdin.read(2)
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Ultimate fallback to regular input
        return input().strip() or '\r'

# Theme colors
LIME_PRIMARY = "#32CD32"      # Lime green
LIME_SECONDARY = "#9AFF9A"    # Light lime
LIME_ACCENT = "#00FF00"       # Bright green
LIME_DARK = "#228B22"         # Dark green

class DotfilesManager:
    def __init__(self):
        self.running = True
        self.selected_option = 0  # Currently selected menu option (0-4)
        self.menu_options = [
            ("1", "🍻  View Modified Files", "Check which dotfiles have been modified"),
            ("2", "🐙  Add/Remove Files", "Manage tracked dotfiles"),
            ("3", "🐒  Settings", "Configure paths and options"),
            ("4", "🖕  Restore Files", "Restore backed up configurations"),
            ("5", "💀  Quit", "Exit the dotfiles manager")
        ]
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                return {
                    'search_paths': config.get('include_paths', ['~/.config']),
                    'file_patterns': config.get('include_extensions', ['*.ini', '*.conf', '*.json']),
                    'exclude_patterns': config.get('exclude_paths', []) + config.get('exclude_extensions', []),
                    'max_depth': 5,
                    'show_hidden': True
                }
        except FileNotFoundError:
            console.print("[red]Error: config.json not found[/red]")
            return {
                'search_paths': ['~/.config'],
                'file_patterns': ['*.ini', '*.conf', '*.json'],
                'exclude_patterns': ['*/cache/*', '*/.git/*'],
                'max_depth': 5,
                'show_hidden': True
            }
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON in config.json[/red]")
            return {
                'search_paths': ['~/.config'],
                'file_patterns': ['*.ini', '*.conf', '*.json'],
                'exclude_patterns': ['*/cache/*', '*/.git/*'],
                'max_depth': 5,
                'show_hidden': True
            }

    def display_header(self):
        """Display the beautiful header with lime theme"""
        title = Text("🌿 WAYFIRE DOTFILES MANAGER 🌿", style=f"bold {LIME_PRIMARY}")
        subtitle = Text("Manage your Wayfire configuration files with style", style=LIME_SECONDARY)

        header_content = Align.center(
            Text.assemble(
                title, "\n",
                subtitle
            )
        )

        header_panel = Panel(
            header_content,
            style=LIME_DARK,
            border_style=LIME_ACCENT,
            box=box.DOUBLE,
            padding=(1, 2)
        )

        console.print(header_panel)
        console.print()

    def create_menu_items(self):
        """Create ultra-compact centered menu items with equal row lengths"""
        menu_lines = []

        # Find the longest text to make all rows equal length
        max_length = 0
        all_texts = []

        for i, (num, title, desc) in enumerate(self.menu_options):
            if i == self.selected_option:
                text_content = f"► [{num}] {title}"
            else:
                text_content = f"· [{num}] {title}"
            all_texts.append(text_content)
            max_length = max(max_length, len(text_content))

        # Create menu items with equal lengths
        for i, (num, title, desc) in enumerate(self.menu_options):
            is_selected = (i == self.selected_option)
            text_content = all_texts[i]

            # Add left margin and pad to max length for equal row widths
            margin = "        "  # 8 spaces left margin
            padded_text = margin + text_content + " " * (max_length - len(text_content))

            # Create format without row highlighting
            if is_selected:
                if num == "5":  # Quit option
                    line_text = Text(padded_text, style=f"bold red")
                    border_char = "═"
                    border_color = "red"
                else:
                    line_text = Text(padded_text, style=f"bold {LIME_ACCENT}")
                    border_char = "═"
                    border_color = LIME_ACCENT
            else:
                line_text = Text(padded_text, style="dim white")  # Light gray for unselected
                if num == "5":  # Quit option
                    border_char = "─"
                    border_color = "#FF6B6B"
                else:
                    border_char = "─"
                    border_color = LIME_DARK

            # Add the text line
            menu_lines.append(line_text)

            # Add bottom border line with same length including margin
            border_line = Text(margin + border_char * max_length, style=border_color)
            menu_lines.append(border_line)

        return menu_lines

    def display_menu(self):
        """Display styled compact menu"""
        console.clear()

        # Create menu items
        menu_lines = self.create_menu_items()

        # Create smaller header inside panel
        inner_header = Text("Manage your Wayfire configuration files", style=LIME_SECONDARY, justify="center")

        # Create renderable content for the panel with inner header
        from rich.console import Group
        menu_content = Group(inner_header, Text(""), *menu_lines)

        # Wrap menu in a panel with title
        menu_panel = Panel(
            menu_content,
            title="🐉 WAYFIRE DOTFILES MANAGER",
            title_align="center",
            style="#F8FFF8",
            border_style=LIME_PRIMARY,
            box=box.ROUNDED,
            padding=(1, 1)
        )

        console.print(menu_panel)

        # Show navigation instructions at bottom
        console.print(Text("↑↓/ws: navigate • Enter: select • 1-5: direct • q: quit", style=LIME_SECONDARY), justify="center")

    def handle_menu_navigation(self):
        """Handle universal arrow key navigation using getch"""

        try:
            while True:
                # Get single character input (handles arrow keys automatically)
                key = get_key()

                # Handle arrow keys
                if key == '\x1b[A':  # Up arrow
                    self.selected_option = (self.selected_option - 1) % 5
                    self.display_menu()
                elif key == '\x1b[B':  # Down arrow
                    self.selected_option = (self.selected_option + 1) % 5
                    self.display_menu()

                # Handle regular keys
                elif key.lower() == 'w' or key.lower() == 'k':  # Up
                    self.selected_option = (self.selected_option - 1) % 5
                    self.display_menu()
                elif key.lower() == 's' or key.lower() == 'j':  # Down
                    self.selected_option = (self.selected_option + 1) % 5
                    self.display_menu()
                elif key == '\r' or key == '\n':  # Enter
                    return self.selected_option + 1
                elif key.lower() == 'q' or key == '\x1b':  # Quit (q or Esc)
                    return 5
                elif key.isdigit() and 1 <= int(key) <= 5:  # Direct number selection
                    return int(key)

        except KeyboardInterrupt:
            return 5

    def view_modified_files(self):
        """Menu option 1: View modified files"""
        console.print(Panel(
            Text("🔍 MODIFIED FILES VIEWER\n\nThis feature will scan for modified dotfiles...",
                 style=LIME_PRIMARY),
            title="View Modified Files",
            border_style=LIME_ACCENT
        ))
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press Enter to continue...[/]")
        input()

    def is_path_allowed(self, path):
        """Check if a path is within allowed search paths"""
        expanded_path = os.path.abspath(path)
        search_paths = [os.path.abspath(os.path.expanduser(p)) for p in self.config.get('search_paths', ['~'])]
        
        # Allow if path is within any search path or is a parent of search paths
        for search_path in search_paths:
            if expanded_path == search_path or expanded_path.startswith(search_path + os.sep):
                return True
            # Also allow parent directories that lead to search paths
            if search_path.startswith(expanded_path + os.sep):
                return True
        
        return False
    
    def should_exclude_item(self, item_path, item_name):
        """Check if an item should be excluded based on patterns"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        
        # Check against full path
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(item_path, pattern) or fnmatch.fnmatch(item_name, pattern):
                return True
            # Also check relative patterns
            if pattern.startswith('*/'):
                if fnmatch.fnmatch(os.path.basename(item_path), pattern[2:]):
                    return True
        
        return False
    
    def should_show_directory(self, dir_path):
        """Check if a directory should be shown (contains allowed content or leads to search paths)"""
        expanded_path = os.path.abspath(dir_path)
        search_paths = [os.path.abspath(os.path.expanduser(p)) for p in self.config.get('search_paths', ['~'])]
        
        # Show if directory is a search path or within one
        for search_path in search_paths:
            if expanded_path == search_path or expanded_path.startswith(search_path + os.sep):
                return True
            # Show if directory is on the path to a search path
            if search_path.startswith(expanded_path + os.sep):
                return True
        
        return False
    
    def should_show_file(self, file_path, file_name):
        """Check if a file should be shown based on patterns and location"""
        # Must be in allowed path
        if not self.is_path_allowed(file_path):
            return False
        
        # Must match file patterns
        file_patterns = self.config.get('file_patterns', ['*'])
        if not any(fnmatch.fnmatch(file_name, pattern) for pattern in file_patterns):
            return False
        
        return True
    
    def get_directory_contents(self, directory):
        """Get files and directories in the current directory, filtered by config"""
        items = []
        
        try:
            # Add parent directory option (except for root and home)
            parent_dir = os.path.dirname(directory)
            if directory != '/' and parent_dir != directory:
                items.append({'path': '..', 'type': 'parent', 'full_path': parent_dir})
            
            # Get all items in current directory
            for item_name in sorted(os.listdir(directory)):
                item_path = os.path.join(directory, item_name)
                
                # Skip hidden files unless configured to show them
                if item_name.startswith('.') and not self.config.get('show_hidden', True):
                    continue
                
                # Skip if matches exclude patterns
                if self.should_exclude_item(item_path, item_name):
                    continue
                
                if os.path.isdir(item_path):
                    # Show directory if it should be shown (contains relevant content or on path to search paths)
                    if self.should_show_directory(item_path):
                        items.append({'path': item_name, 'type': 'directory', 'full_path': item_path})
                elif os.path.isfile(item_path):
                    # Show file if it matches patterns and is in allowed location
                    if self.should_show_file(item_path, item_name):
                        items.append({'path': item_name, 'type': 'file', 'full_path': item_path})
            
        except PermissionError:
            console.print(f"[red]Permission denied accessing {directory}[/red]")
            
        return items
    
    def get_files_in_directory_recursive(self, directory):
        """Get all files in a directory recursively that match our patterns"""
        files_in_dir = []
        
        for pattern in self.config.get('file_patterns', []):
            for file_path in glob.glob(os.path.join(directory, '**', pattern), recursive=True):
                # Skip if matches exclude patterns
                if any(fnmatch.fnmatch(file_path, exclude) for exclude in self.config.get('exclude_patterns', [])):
                    continue
                files_in_dir.append(file_path)
                
        return files_in_dir
    
    def file_browser(self):
        """Interactive file browser with multi-column layout, scrolling, and search"""
        current_dir = os.path.expanduser('~')
        selected_items = set()
        current_selection = 0
        scroll_offset_row = 0
        scroll_offset_col = 0
        last_items = []
        need_refresh = True
        search_term = ""
        search_mode = False
        last_terminal_size = None
        
        def filter_items(items, search):
            """Filter items based on search term"""
            if not search:
                return items
            search_lower = search.lower()
            return [item for item in items if search_lower in item['path'].lower()]
        
        while True:
            all_items = self.get_directory_contents(current_dir)
            items = filter_items(all_items, search_term)
            
            # Get terminal size
            terminal_size = console.size
            terminal_height = terminal_size.height
            
            # Only refresh if items changed, terminal resized, or explicit refresh needed
            terminal_changed = last_terminal_size != terminal_size
            items_changed = items != last_items
            
            if items_changed or need_refresh or terminal_changed:
                last_items = items[:]
                last_terminal_size = terminal_size
                need_refresh = False
                
                # Ensure current_selection is within bounds
                if current_selection >= len(items):
                    current_selection = len(items) - 1 if items else 0
                
                # Fixed 2-column layout
                columns = 2
                max_item_width = (terminal_size.width - 10) // columns  # Account for panel borders and spacing
                
                # Calculate visible area (reserve lines for panel borders, internal footer, and search)
                visible_height = max(1, terminal_height - 12)  # Account for panel borders, footer, and search line
                visible_rows = visible_height
                items_per_screen = columns * visible_rows
                
                # Calculate current row and column
                if items:
                    current_row = current_selection // columns
                    current_col = current_selection % columns
                    
                    # Adjust vertical scroll offset to keep current selection visible
                    if current_row < scroll_offset_row:
                        scroll_offset_row = current_row
                    elif current_row >= scroll_offset_row + visible_rows:
                        scroll_offset_row = current_row - visible_rows + 1
                        
                    # No horizontal scrolling needed with current layout
                    scroll_offset_col = 0
                else:
                    current_row = current_col = 0
                
                # Clear screen and prepare content
                console.clear()
                
                # Prepare file list content in columns
                file_content = []
                
                if not items:
                    file_content.append(Text("Empty directory or no accessible items", style="red"))
                else:
                    # Create grid layout
                    for row in range(visible_rows):
                        actual_row = row + scroll_offset_row
                        row_items = []
                        
                        for col in range(columns):
                            item_index = actual_row * columns + col
                            
                            if item_index < len(items):
                                item = items[item_index]
                                item_path = item['full_path'] if item['type'] != 'parent' else item['path']
                                item_type = item['type']
                                display_name = item['path']
                                
                                # Truncate long names
                                if len(display_name) > max_item_width - 8:
                                    display_name = display_name[:max_item_width - 11] + "..."
                                
                                # Don't show checkbox for parent directory
                                if item_type == 'parent':
                                    checkbox = " "
                                    icon = "⬅️"
                                else:
                                    checkbox = "☑️" if item_path in selected_items else "☐"
                                    icon = "📂" if item_type == 'directory' else "📄"
                                
                                # Highlight current selection
                                is_current = item_index == current_selection
                                
                                if is_current:
                                    style = f"bold {LIME_ACCENT}"
                                    prefix = "►"
                                elif item_path in selected_items and item_type != 'parent':
                                    style = f"bold {LIME_PRIMARY}"
                                    prefix = " "
                                else:
                                    style = "white"
                                    prefix = " "
                                
                                # Format item with fixed width
                                item_display = f"{prefix}{checkbox} {icon} {display_name}"
                                item_display = item_display.ljust(max_item_width)
                                row_items.append(Text(item_display, style=style))
                            else:
                                # Empty cell
                                row_items.append(Text("".ljust(max_item_width)))
                        
                        if row_items and any(item.plain for item in row_items if item.plain.strip()):
                            file_content.append(Columns(row_items, padding=(0, 1), expand=False))
                    
                    # Add scroll indicator if needed
                    total_rows = (len(items) + columns - 1) // columns
                    if total_rows > visible_rows:
                        file_content.append(Text(""))  # Empty line
                        scroll_info = Text(f"Showing rows {scroll_offset_row + 1}-{min(scroll_offset_row + visible_rows, total_rows)} of {total_rows}", style=LIME_SECONDARY)
                        file_content.append(scroll_info)
                
                # Add search line
                if search_mode:
                    search_display = f"Search: {search_term}_"
                    search_style = f"bold {LIME_ACCENT}"
                elif search_term:
                    search_display = f"Filter: {search_term} (showing {len(items)}/{len(all_items)})"
                    search_style = LIME_PRIMARY
                else:
                    search_display = "Press / to search"
                    search_style = LIME_SECONDARY
                
                file_content.append(Text(""))  # Empty line
                file_content.append(Text(search_display, style=search_style))
                
                # Add footer content inside panel
                file_content.append(Text(""))  # Empty line
                file_content.append(Text("─" * min(60, terminal_size.width - 4), style=LIME_SECONDARY))
                if search_mode:
                    file_content.append(Text("Type to search • Enter: confirm • Esc: cancel search", style=LIME_SECONDARY))
                else:
                    file_content.append(Text("↑↓←→: navigate • Enter: open • Space: select • /: search • Tab: add • q: cancel", style=LIME_SECONDARY))
                file_content.append(Text(f"Selected: {len(selected_items)} items • Items: {len(items)} • Cols: {columns}", style=LIME_SECONDARY))
                
                # Header with current directory
                current_dir_display = current_dir.replace(os.path.expanduser('~'), '~')
                
                # Only clear screen when really needed to reduce flicker
                console.clear()
                
                # Create panel with all content inside, ensuring proper width
                console.print(Panel(
                    Group(*file_content),
                    title=f"📁 FILE BROWSER - {current_dir_display}",
                    title_align="left",
                    border_style=LIME_ACCENT,
                    padding=(0, 1),
                    width=terminal_size.width
                ))
            
            # Handle input
            key = get_key()
            
            if search_mode:
                # Search mode input handling
                if key == '\r' or key == '\n':  # Enter - confirm search
                    search_mode = False
                    need_refresh = True
                elif key == '\x1b':  # Escape - cancel search
                    search_mode = False
                    search_term = ""
                    need_refresh = True
                elif key == '\x7f' or key == '\b':  # Backspace
                    if search_term:
                        search_term = search_term[:-1]
                        need_refresh = True
                elif len(key) == 1 and key.isprintable():  # Regular character
                    search_term += key
                    current_selection = 0  # Reset selection when searching
                    need_refresh = True
            else:
                # Normal navigation mode
                if key == '\x1b[A' or key.lower() == 'k':  # Up
                    if items:
                        if current_selection >= columns:
                            current_selection -= columns
                        else:
                            # Wrap to bottom row, same column
                            bottom_row_start = ((len(items) - 1) // columns) * columns
                            col_in_current_row = current_selection % columns
                            current_selection = min(bottom_row_start + col_in_current_row, len(items) - 1)
                        need_refresh = True
                elif key == '\x1b[B' or key.lower() == 'j':  # Down
                    if items:
                        if current_selection + columns < len(items):
                            current_selection += columns
                        else:
                            # Wrap to top row, same column
                            col_in_current_row = current_selection % columns
                            current_selection = min(col_in_current_row, len(items) - 1)
                        need_refresh = True
                elif key == '\x1b[D' or key.lower() == 'h':  # Left
                    if items:
                        current_selection = (current_selection - 1) % len(items)
                        need_refresh = True
                elif key == '\x1b[C' or key.lower() == 'l':  # Right
                    if items:
                        current_selection = (current_selection + 1) % len(items)
                        need_refresh = True
                elif key == '\r' or key == '\n':  # Enter - navigate into directory
                    if items and current_selection < len(items):
                        current_item = items[current_selection]
                        if current_item['type'] == 'directory':
                            current_dir = current_item['full_path']
                            current_selection = 0
                            scroll_offset = 0
                            search_term = ""  # Clear search when navigating
                            need_refresh = True
                        elif current_item['type'] == 'parent':
                            current_dir = current_item['full_path']
                            current_selection = 0
                            scroll_offset = 0
                            search_term = ""  # Clear search when navigating
                            need_refresh = True
                elif key == ' ':  # Space - toggle selection (not for parent dir)
                    if items and current_selection < len(items):
                        current_item = items[current_selection]
                        if current_item['type'] != 'parent':
                            item_path = current_item['full_path']
                            if item_path in selected_items:
                                selected_items.remove(item_path)
                            else:
                                selected_items.add(item_path)
                            need_refresh = True
                elif key == '/':  # Start search
                    search_mode = True
                    search_term = ""
                    need_refresh = True
                elif key == '\t':  # Tab - confirm selection and add to git
                    return list(selected_items)
                elif key.lower() == 'q' or key == '\x1b':  # Quit
                    return []
    
    def is_protected_file(self, file_path):
        """Check if file is protected from overwriting"""
        current_script = os.path.abspath(__file__)
        config_file = os.path.abspath('config.json')
        abs_path = os.path.abspath(file_path)
        
        return abs_path == current_script or abs_path == config_file
    
    def copy_file_to_dotfiles(self, source_path, current_dir):
        """Copy a file to the dotfiles directory, preserving relative structure"""
        home_dir = os.path.expanduser('~')
        
        # Calculate relative path from home
        if source_path.startswith(home_dir):
            rel_path = os.path.relpath(source_path, home_dir)
        else:
            # For files outside home, use basename
            rel_path = os.path.basename(source_path)
        
        # Target path in dotfiles directory
        target_path = os.path.join(current_dir, rel_path)
        
        # Create target directory if needed
        target_dir = os.path.dirname(target_path)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        return target_path
    
    def copy_items_to_dotfiles(self, selected_paths):
        """Copy selected files and directories to dotfiles directory, then add to git"""
        if not selected_paths:
            console.print(f"[{LIME_SECONDARY}]No items selected.[/]")
            return
        
        current_dir = os.getcwd()
        
        # Expand directories to include all their files
        all_files_to_process = []
        
        for path in selected_paths:
            if os.path.isfile(path):
                all_files_to_process.append(path)
            elif os.path.isdir(path):
                # Get all matching files in the directory recursively
                dir_files = self.get_files_in_directory_recursive(path)
                all_files_to_process.extend(dir_files)
                console.print(f"[{LIME_SECONDARY}]📂 Directory {path.replace(os.path.expanduser('~'), '~')} contains {len(dir_files)} files[/]")
        
        # Remove duplicates
        all_files_to_process = list(set(all_files_to_process))
        
        console.print(Panel(
            Text(f"Copying {len(all_files_to_process)} files to dotfiles directory and adding to git...", style=LIME_PRIMARY),
            title="Copying and Adding Files",
            border_style=LIME_ACCENT
        ))
        
        copied_files = []
        skipped_files = []
        failed_files = []
        
        for source_path in all_files_to_process:
            try:
                # Check if file is already in dotfiles directory
                if os.path.dirname(os.path.abspath(source_path)) == current_dir:
                    # File is already in dotfiles directory
                    if self.is_protected_file(source_path):
                        skipped_files.append((source_path, "protected file"))
                        console.print(f"[yellow]⚠️[/yellow] {source_path.replace(os.path.expanduser('~'), '~')} (protected)")
                        continue
                    else:
                        # Add directly to git
                        result = subprocess.run(['git', 'add', source_path], 
                                              capture_output=True, text=True, check=True)
                        copied_files.append(source_path)
                        console.print(f"[{LIME_PRIMARY}]✓[/] {source_path.replace(os.path.expanduser('~'), '~')} (already in dotfiles)")
                        continue
                
                # Calculate target path
                target_path = self.copy_file_to_dotfiles(source_path, current_dir)
                
                # Check if target would overwrite protected files
                if self.is_protected_file(target_path):
                    skipped_files.append((source_path, "would overwrite protected file"))
                    console.print(f"[yellow]⚠️[/yellow] {source_path.replace(os.path.expanduser('~'), '~')} (would overwrite protected file)")
                    continue
                
                # Copy the file
                shutil.copy2(source_path, target_path)
                
                # Add to git
                result = subprocess.run(['git', 'add', target_path], 
                                      capture_output=True, text=True, check=True)
                
                copied_files.append(target_path)
                console.print(f"[{LIME_PRIMARY}]✓[/] {source_path.replace(os.path.expanduser('~'), '~')} → {os.path.relpath(target_path)}")
                
            except subprocess.CalledProcessError as e:
                failed_files.append((source_path, f"git error: {e.stderr.strip()}"))
                console.print(f"[red]✗[/red] {source_path.replace(os.path.expanduser('~'), '~')} (git error)")
            except Exception as e:
                failed_files.append((source_path, str(e)))
                console.print(f"[red]✗[/red] {source_path.replace(os.path.expanduser('~'), '~')} (copy error)")
        
        # Summary
        console.print("\n" + "─" * 60)
        console.print(f"[{LIME_PRIMARY}]Successfully copied and added: {len(copied_files)} files[/]")
        if skipped_files:
            console.print(f"[yellow]Skipped: {len(skipped_files)} files (protected)[/yellow]")
        if failed_files:
            console.print(f"[red]Failed: {len(failed_files)} files[/red]")
            
        console.print(f"\n[{LIME_SECONDARY}]Press Enter to continue...[/]")
        input()
    
    def add_remove_files(self):
        """Menu option 2: Add/Remove files with file browser"""
        selected_items = self.file_browser()
        
        if selected_items:
            self.copy_items_to_dotfiles(selected_items)

    def settings(self):
        """Menu option 3: Settings"""
        console.print(Panel(
            Text("⚙️ SETTINGS CONFIGURATION\n\nConfigure search paths, exclude patterns, and more...",
                 style=LIME_PRIMARY),
            title="Settings",
            border_style=LIME_ACCENT
        ))
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press Enter to continue...[/]")
        input()

    def restore_files(self):
        """Menu option 4: Restore files"""
        console.print(Panel(
            Text("🔄 FILE RESTORATION\n\nRestore your dotfiles from backups...",
                 style=LIME_PRIMARY),
            title="Restore Files",
            border_style=LIME_ACCENT
        ))
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press Enter to continue...[/]")
        input()

    def quit_application(self):
        """Menu option 5: Quit"""
        goodbye_text = Text.assemble(
            ("Thank you for using ", LIME_SECONDARY),
            ("Wayfire Dotfiles Manager", f"bold {LIME_PRIMARY}"),
            ("! 🌿", LIME_ACCENT)
        )

        goodbye_panel = Panel(
            Align.center(goodbye_text),
            style="#F0FFF0",
            border_style=LIME_PRIMARY,
            box=box.DOUBLE
        )

        console.print(goodbye_panel)
        self.running = False

    def run(self):
        """Main application loop"""
        try:
            while self.running:
                self.display_menu()
                choice = self.handle_menu_navigation()

                console.clear()

                if choice == 1:
                    self.view_modified_files()
                elif choice == 2:
                    self.add_remove_files()
                elif choice == 3:
                    self.settings()
                elif choice == 4:
                    self.restore_files()
                elif choice == 5:
                    self.quit_application()

        except KeyboardInterrupt:
            console.print(f"\n[{LIME_ACCENT}]Interrupted! Goodbye! 👋[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def main():
    """Entry point"""
    # Check if we're in the virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        console.print("[yellow]Warning: You might want to activate the virtual environment first:[/]")
        console.print("[cyan]source venv/bin/activate[/]")
        console.print()

    # Create and run the dotfiles manager
    manager = DotfilesManager()
    manager.run()

if __name__ == "__main__":
    main()
