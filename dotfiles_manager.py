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

# Key codes constants for better readability
class KeyCodes:
    """Terminal key codes used throughout the application"""
    # Control keys
    ESC = '\x1b'         # Escape key
    ENTER = '\r'         # Enter/Return key
    CTRL_C = '\x03'      # Ctrl+C interrupt

    # Backspace variations (different terminals)
    BACKSPACE = '\x7f'   # DEL character (most common)
    BACKSPACE_ALT = '\x08'  # BS character (some terminals)

    # Arrow keys (ANSI escape sequences)
    ARROW_UP = '\x1b[A'     # Up arrow
    ARROW_DOWN = '\x1b[B'   # Down arrow
    ARROW_RIGHT = '\x1b[C'  # Right arrow
    ARROW_LEFT = '\x1b[D'   # Left arrow

    # Function keys
    F1 = '\x1bOP'        # F1 key
    F2 = '\x1bOQ'        # F2 key
    F3 = '\x1bOR'        # F3 key
    F4 = '\x1bOS'        # F4 key

    # Special keys
    HOME = '\x1b[H'      # Home key
    END = '\x1b[F'       # End key
    PAGE_UP = '\x1b[5~'  # Page Up
    PAGE_DOWN = '\x1b[6~' # Page Down
    DELETE = '\x1b[3~'   # Delete key

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
                return input().strip() or KeyCodes.ENTER

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)

                # Handle ESC sequences - simple approach
                if key == KeyCodes.ESC:  # ESC sequences (arrows, function keys, etc.)
                    # Always read 2 more characters for sequences like ESC[A
                    try:
                        additional = sys.stdin.read(2)
                        full_sequence = key + additional
                        # Check if this is a valid arrow key sequence
                        if full_sequence in [KeyCodes.ARROW_UP, KeyCodes.ARROW_DOWN,
                                           KeyCodes.ARROW_LEFT, KeyCodes.ARROW_RIGHT]:
                            return full_sequence
                        # If it's not a recognized sequence, check if we got nothing (standalone ESC)
                        if len(additional) == 0:
                            return KeyCodes.ESC  # Standalone ESC
                        # Otherwise return the full sequence anyway
                        return full_sequence
                    except:
                        return KeyCodes.ESC  # Standalone ESC on error

                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Ultimate fallback to regular input
        return input().strip() or KeyCodes.ENTER

def wait_for_key():
    """Wait for any key press, supporting ESC to cancel"""
    key = get_key()
    return key not in [KeyCodes.ESC, 'q', 'Q']

def show_popup_notification(message, duration=1.0, style="green"):
    """Show a centered popup notification for a specified duration"""
    import time

    # Clear screen and get terminal size
    console.clear()
    terminal_size = console.size

    # Create centered popup panel
    popup_panel = Panel(
        Align.center(Text(message, style=f"bold {style}")),
        title="📢 NOTIFICA",
        title_align="center",
        border_style=style,
        padding=(1, 2)
    )

    # Print some empty lines to center vertically
    vertical_padding = max(0, (terminal_size.height // 2) - 5)
    for _ in range(vertical_padding):
        console.print("")

    # Show the popup
    console.print(popup_panel)

    # Wait for the specified duration
    time.sleep(duration)

def get_confirmation(prompt, default='n'):
    """Get s/n confirmation with ESC support"""
    while True:
        console.print(f"[yellow]{prompt} (s/n): [/]", end="")
        key = get_key()
        console.print(key)  # Echo the key

        if key == KeyCodes.ESC or key.lower() == 'q':
            return False  # ESC or Q cancels (ma non mostrato nel prompt)
        elif key.lower() == 's':
            return True
        elif key.lower() == 'n':
            return False
        elif key == KeyCodes.ENTER:
            return default.lower() == 's'

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
        config_file = 'config.json'
        default_config = {
            'git_dir': '~/.dotfiles.git',
            'work_tree': '~',
            'remote': ''
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                result = default_config.copy()
                result.update(config)
                return result
        except FileNotFoundError:
            # Create config file with defaults
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON in config.json[/red]")
            return default_config

    def save_config(self, config=None):
        """Save configuration to config.json"""
        if config is None:
            config = self.config
        
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
            return False

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

    def display_menu(self):
        """Display the main menu and handle navigation - simple approach"""
        console.clear()
        
        # Create menu content
        menu_lines = []
        for i, (num, title, desc) in enumerate(self.menu_options):
            if i == self.selected_option:
                if num == "5":  # Quit option
                    menu_lines.append(Text(f"        ► [{num}] {title}", style="bold red"))
                else:
                    menu_lines.append(Text(f"        ► [{num}] {title}", style=f"bold {LIME_ACCENT}"))
            else:
                menu_lines.append(Text(f"        · [{num}] {title}", style="dim white"))

        # Create header
        header = Text("Manage your Wayfire configuration files", style=LIME_SECONDARY, justify="center")
        
        # Create complete menu content
        menu_content = Group(
            header,
            Text(""),
            *menu_lines,
            Text(""),
            Text("↑↓/ws: navigate • Enter: select • 1-5: direct • q: quit", style=LIME_SECONDARY, justify="center")
        )
        
        # Display menu panel
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

    def handle_menu_navigation(self):
        """Handle menu navigation with simple clear/print approach"""
        while True:
            self.display_menu()

            try:
                key = get_key()

                # Handle arrow keys
                if key == KeyCodes.ARROW_UP:
                    # Navigate up in menu (Arrow Up key)
                    self.selected_option = (self.selected_option - 1) % 5
                elif key == KeyCodes.ARROW_DOWN:
                    # Navigate down in menu (Arrow Down key)
                    self.selected_option = (self.selected_option + 1) % 5
                # Handle regular keys (WASD/HJKL style navigation)
                elif key.lower() == 'w' or key.lower() == 'k':  # Up (W/K keys)
                    self.selected_option = (self.selected_option - 1) % 5
                elif key.lower() == 's' or key.lower() == 'j':  # Down (S/J keys)
                    self.selected_option = (self.selected_option + 1) % 5
                elif key == KeyCodes.ENTER or key == '\n':
                    # Select current menu option (Enter key)
                    return self.selected_option + 1
                elif key.lower() == 'q' or key == KeyCodes.ESC:
                    # Quit application (Q key or Escape)
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
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press any key to continue (ESC to cancel)...[/]")
        wait_for_key()

    def get_directory_contents(self, directory):
        """Get files and directories in the current directory"""
        items = []

        try:
            # Add parent directory option (except for root and home)
            parent_dir = os.path.dirname(directory)
            if directory != '/' and parent_dir != directory:
                items.append({'path': '..', 'type': 'parent', 'full_path': parent_dir})

            # Get all items in current directory
            for item_name in sorted(os.listdir(directory)):
                item_path = os.path.join(directory, item_name)

                if os.path.isdir(item_path):
                    items.append({'path': item_name, 'type': 'directory', 'full_path': item_path})
                elif os.path.isfile(item_path):
                    items.append({'path': item_name, 'type': 'file', 'full_path': item_path})

        except PermissionError:
            console.print(f"[red]Permission denied accessing {directory}[/red]")

        return items
    
    
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
                
                # Calculate visible area (reserve lines for panel borders, footer, and instructions)
                visible_height = max(1, terminal_height - 15)  # More conservative height calculation
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
                
                # Only clear screen when content changes significantly
                
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
                
                # Clear screen and display panel
                console.clear()
                console.print(Panel(
                    Group(*file_content),
                    title=f"📁 FILE BROWSER - {current_dir_display}",
                    title_align="left",
                    border_style=LIME_ACCENT,
                    padding=(0, 1)
                ))
            
            # Handle input
            key = get_key()
            
            if search_mode:
                # Search mode input handling
                if key == KeyCodes.ENTER or key == '\n':
                    # Confirm search (Enter key)
                    search_mode = False
                    need_refresh = True
                elif key == KeyCodes.ESC:
                    # Cancel search (Escape key)
                    search_mode = False
                    search_term = ""
                    need_refresh = True
                elif key == KeyCodes.BACKSPACE or key == '\b':
                    # Remove character from search (Backspace key)
                    if search_term:
                        search_term = search_term[:-1]
                        need_refresh = True
                elif len(key) == 1 and key.isprintable():
                    # Add character to search term (printable characters)
                    search_term += key
                    current_selection = 0  # Reset selection when searching
                    need_refresh = True
            else:
                # Normal navigation mode
                if key == KeyCodes.ARROW_UP or key.lower() == 'k':
                    # Navigate up in grid (Arrow Up or K key)
                    if items:
                        if current_selection >= columns:
                            current_selection -= columns
                        else:
                            # Wrap to bottom row, same column
                            bottom_row_start = ((len(items) - 1) // columns) * columns
                            col_in_current_row = current_selection % columns
                            current_selection = min(bottom_row_start + col_in_current_row, len(items) - 1)
                        need_refresh = True
                elif key == KeyCodes.ARROW_DOWN or key.lower() == 'j':
                    # Navigate down in grid (Arrow Down or J key)
                    if items:
                        if current_selection + columns < len(items):
                            current_selection += columns
                        else:
                            # Wrap to top row, same column
                            col_in_current_row = current_selection % columns
                            current_selection = min(col_in_current_row, len(items) - 1)
                        need_refresh = True
                elif key == KeyCodes.ARROW_LEFT or key.lower() == 'h':
                    # Navigate left in grid (Arrow Left or H key)
                    if items:
                        current_selection = (current_selection - 1) % len(items)
                        need_refresh = True
                elif key == KeyCodes.ARROW_RIGHT or key.lower() == 'l':
                    # Navigate right in grid (Arrow Right or L key)
                    if items:
                        current_selection = (current_selection + 1) % len(items)
                        need_refresh = True
                elif key == KeyCodes.ENTER or key == '\n':
                    # Enter directory or select file (Enter key)
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
                elif key.lower() == 'q' or key == KeyCodes.ESC:
                    # Quit file browser (Q key or Escape)
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
            
        console.print(f"\n[{LIME_SECONDARY}]Press any key to continue (ESC to cancel)...[/]")
        wait_for_key()
    
    def add_remove_files(self):
        """Menu option 2: Add/Remove files with file browser"""
        selected_items = self.file_browser()
        
        if selected_items:
            self.copy_items_to_dotfiles(selected_items)

    def settings(self):
        """Menu option 3: Settings - Display settings submenu"""
        selected_option = 0
        settings_options = [
            ("1", "✏️  Modifica Settings", "Edit configuration settings"),
            ("2", "🚀  Inizializza Repo Git", "Initialize bare git repository"),
            ("3", "🔙  Torna al Menu", "Return to main menu")
        ]
        
        while True:
            console.clear()
            
            # Create menu content
            menu_lines = []
            for i, (num, title, desc) in enumerate(settings_options):
                if i == selected_option:
                    menu_lines.append(Text(f"        ► [{num}] {title}", style=f"bold {LIME_ACCENT}"))
                else:
                    menu_lines.append(Text(f"        · [{num}] {title}", style="dim white"))

            # Create header
            header = Text("Configure your dotfiles manager", style=LIME_SECONDARY, justify="center")
            
            # Create complete menu content
            menu_content = Group(
                header,
                Text(""),
                *menu_lines,
                Text(""),
                Text("↑↓/ws: navigate • Enter: select • 1-3: direct • q: back", style=LIME_SECONDARY, justify="center")
            )
            
            # Display menu panel
            menu_panel = Panel(
                menu_content,
                title="⚙️ SETTINGS",
                title_align="center",
                style="#F8FFF8",
                border_style=LIME_PRIMARY,
                box=box.ROUNDED,
                padding=(1, 1)
            )
            
            console.print(menu_panel)
            
            # Handle input
            try:
                key = get_key()
                
                # Handle arrow keys
                if key == KeyCodes.ARROW_UP:
                    # Navigate up in settings menu (Arrow Up key)
                    selected_option = (selected_option - 1) % 3
                elif key == KeyCodes.ARROW_DOWN:
                    # Navigate down in settings menu (Arrow Down key)
                    selected_option = (selected_option + 1) % 3
                # Handle regular keys (WASD/HJKL style navigation)
                elif key.lower() == 'w' or key.lower() == 'k':  # Up (W/K keys)
                    selected_option = (selected_option - 1) % 3
                elif key.lower() == 's' or key.lower() == 'j':  # Down (S/J keys)
                    selected_option = (selected_option + 1) % 3
                elif key == KeyCodes.ENTER or key == '\n':
                    # Select current menu option (Enter key)
                    choice = selected_option + 1
                    break
                elif key.lower() == 'q' or key == KeyCodes.ESC:
                    # Go back to main menu (Q key or Escape)
                    return
                elif key.isdigit() and 1 <= int(key) <= 3:  # Direct number selection
                    choice = int(key)
                    break
                    
            except KeyboardInterrupt:
                return
        
        # Handle menu choice
        if choice == 1:
            console.clear()
            self.edit_settings()
        elif choice == 2:
            console.clear()
            self.initialize_git_repo()
        elif choice == 3:
            return  # Back to main menu

    def edit_settings(self):
        """Edit all configuration settings in a compact form interface"""
        console.clear()

        # Create a copy of current config to edit
        temp_config = self.config.copy()

        # Form fields configuration
        fields = [
            {'key': 'git_dir', 'label': 'Git Directory', 'icon': '📁', 'placeholder': '~/.dotfiles.git'},
            {'key': 'work_tree', 'label': 'Work Tree', 'icon': '🌳', 'placeholder': '~'},
            {'key': 'remote', 'label': 'Remote URL', 'icon': '🌐', 'placeholder': 'https://github.com/user/dotfiles.git'}
        ]

        current_field = 0
        editing_mode = False
        edit_value = ""

        while True:
            console.clear()

            # Build compact form content
            form_content = []
            form_content.append(Text("⚙️ CONFIGURAZIONE", style=f"bold {LIME_PRIMARY}"))
            form_content.append(Text("↑↓: naviga  Enter: modifica  s: salva  r: reset campo  q: esci", style=f"{LIME_SECONDARY}"))
            form_content.append(Text(""))

            # Display all fields in compact form
            for i, field in enumerate(fields):
                value = temp_config.get(field['key'], '')
                is_active = (i == current_field)
                is_editing = (is_active and editing_mode)

                # Determine display value
                if is_editing:
                    display_value = edit_value
                    cursor = "█"  # Cursor block
                else:
                    display_value = value if value else f"({field['placeholder']})"
                    cursor = ""

                # Field styling
                if is_active:
                    if is_editing:
                        # Field being edited - green background
                        field_style = f"bold white on {LIME_ACCENT}"
                        value_style = f"bold black on white"
                        prefix = "✏️ "
                    else:
                        # Active field - highlighted
                        field_style = f"bold {LIME_PRIMARY}"
                        value_style = f"bold {LIME_PRIMARY}"
                        prefix = "► "
                else:
                    # Inactive field - dimmed
                    field_style = f"dim {LIME_SECONDARY}"
                    value_style = "dim white"
                    prefix = "  "

                # Compact single-line display
                line = f"{prefix}{field['icon']} {field['label']:<12}: {display_value}{cursor}"
                form_content.append(Text(line, style=field_style if not is_editing else value_style))

            form_content.append(Text(""))
            form_content.append(Text("─────────────────────────────────────", style=LIME_SECONDARY))

            # Status message
            if editing_mode:
                form_content.append(Text(f"✏️ Editing {fields[current_field]['label']} (Enter: conferma, Esc: annulla)", style=f"bold {LIME_ACCENT}"))
            else:
                form_content.append(Text("Controlli: ↑↓ naviga, Enter modifica, s salva tutto, r reset campo corrente", style="white"))

            # Display compact panel
            form_panel = Panel(
                Group(*form_content),
                title="📝 FORM SETTINGS",
                title_align="center",
                border_style=LIME_ACCENT if not editing_mode else LIME_PRIMARY,
                padding=(1, 1)
            )

            console.print(form_panel)

            # Handle input
            try:
                if editing_mode:
                    # In editing mode - handle text input
                    key = get_key()

                    if key == KeyCodes.ESC:
                        # Cancel editing (Escape key)
                        editing_mode = False
                        edit_value = ""

                    elif key == KeyCodes.ENTER:
                        # Confirm editing (Enter/Return key)
                        temp_config[fields[current_field]['key']] = edit_value
                        editing_mode = False
                        edit_value = ""

                    elif key == KeyCodes.BACKSPACE or key == KeyCodes.BACKSPACE_ALT:
                        # Remove last character (Backspace/Delete key)
                        edit_value = edit_value[:-1]

                    elif len(key) == 1 and key.isprintable():
                        # Add printable character
                        edit_value += key

                else:
                    # In navigation mode
                    key = get_key()

                    if key.lower() == 'q' or key == KeyCodes.ESC:
                        return  # Cancel and go back (Q key or Escape)

                    elif key == 's':
                        # Save all changes
                        self.config = temp_config.copy()
                        if self.save_config():
                            show_popup_notification("✓ Configurazioni salvate con successo!", 1.5, LIME_PRIMARY)
                        return

                    elif key == 'r':
                        # Reset current field to default
                        field = fields[current_field]
                        defaults = {
                            'git_dir': '~/.dotfiles.git',
                            'work_tree': '~',
                            'remote': ''
                        }
                        default_value = defaults.get(field['key'], '')
                        current_value = temp_config.get(field['key'], '')

                        # Show elegant confirmation dialog
                        console.clear()

                        confirmation_content = []
                        confirmation_content.append(Text("🔄 RESET CAMPO", style=f"bold {LIME_PRIMARY}"))
                        confirmation_content.append(Text(""))
                        confirmation_content.append(Text(f"Campo: {field['icon']} {field['label']}", style=f"bold {LIME_SECONDARY}"))
                        confirmation_content.append(Text(f"Valore attuale: {current_value if current_value else '(vuoto)'}", style="white"))
                        confirmation_content.append(Text(f"Valore default:  {default_value if default_value else '(vuoto)'}", style=f"{LIME_ACCENT}"))
                        confirmation_content.append(Text(""))
                        confirmation_content.append(Text("Vuoi resettare questo campo al valore di default?", style="yellow"))
                        confirmation_content.append(Text(""))
                        confirmation_content.append(Text("s = Conferma    n = Annulla", style=f"bold {LIME_SECONDARY}"))

                        confirmation_panel = Panel(
                            Group(*confirmation_content),
                            title="⚠️  CONFERMA RESET",
                            title_align="center",
                            border_style="yellow",
                            padding=(1, 1)
                        )

                        console.print(confirmation_panel)

                        if get_confirmation("Vuoi resettare questo campo al valore di default?"):
                            temp_config[field['key']] = default_value
                            show_popup_notification(f"✓ Campo '{field['label']}' resettato!", 1.5, LIME_PRIMARY)

                    elif key == KeyCodes.ARROW_UP:
                        # Move up in form (Arrow Up key)
                        current_field = (current_field - 1) % len(fields)

                    elif key == KeyCodes.ARROW_DOWN:
                        # Move down in form (Arrow Down key)
                        current_field = (current_field + 1) % len(fields)

                    elif key == KeyCodes.ENTER:
                        # Start editing current field (Enter/Return key)
                        editing_mode = True
                        edit_value = temp_config.get(fields[current_field]['key'], '')

            except KeyboardInterrupt:
                if editing_mode:
                    editing_mode = False
                    edit_value = ""
                else:
                    return  # Cancel on Ctrl+C

    def create_gitignore_management(self):
        """Create .gitignore management directory and default .gitignore file"""
        config_dir = os.path.expanduser("~/.config/dotfiles-manager")
        gitignore_path = os.path.join(config_dir, ".gitignore")

        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            console.print(f"[{LIME_PRIMARY}]  ✅ Created config directory: {config_dir}[/]")

        # Create default .gitignore if it doesn't exist
        if not os.path.exists(gitignore_path):
            default_gitignore = """# Default gitignore patterns for dotfiles repository
# Generated automatically by Wayfire Dotfiles Manager

# System and temporary files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
*~
*.tmp
*.temp
*.swp
*.swo
*.bak
*.backup
*.orig
*.rej

# Cache directories
.cache/
*/.cache/
**/.cache/

# User directories that should typically not be tracked
Downloads/
Documents/
Pictures/
Videos/
Music/
Desktop/
Public/
Templates/

# Application caches and state
.local/share/Trash/
.local/share/recently-used.xbel
.local/share/Steam/
.mozilla/
.thunderbird/
.wine/
.PlayOnLinux/

# Development directories
node_modules/
.git/
.svn/
.hg/
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/

# Package manager caches
.npm/
.yarn/
.cargo/
.rustup/
go/pkg/
go/bin/

# Browser profiles (contain sensitive data)
.firefox/
.chromium/
.google-chrome/
snap/

# Logs and temporary data
*.log
logs/
tmp/
temp/

# SSH keys and sensitive files
.ssh/id_*
.ssh/known_hosts
.gnupg/
.password-store/

# Application specific
.steam/
.local/share/Steam/
.minecraft/
.wine/
"""
            with open(gitignore_path, 'w') as f:
                f.write(default_gitignore)
            console.print(f"[{LIME_PRIMARY}]  ✅ Created default .gitignore: {gitignore_path}[/]")
        else:
            console.print(f"[{LIME_PRIMARY}]  ✅ .gitignore already exists: {gitignore_path}[/]")

        return gitignore_path

    def initialize_git_repo(self):
        """Initialize bare git repository for dotfiles management"""
        console.clear()
        
        # Get settings
        git_dir = os.path.expanduser(self.config.get('git_dir', '~/.dotfiles.git'))
        work_tree = os.path.expanduser(self.config.get('work_tree', '~'))
        remote_url = self.config.get('remote', '')
        
        console.print(Panel(
            Group(
                Align.center(Text("✨ INIZIALIZZAZIONE REPOSITORY DOTFILES ✨", style=f"bold {LIME_PRIMARY}")),
                Text(""),
                Align.center(Text("🎯 Configurazione Attuale", style=f"bold {LIME_ACCENT}")),
                Text(""),
                Text(f"📁 Git Directory: {git_dir}", style=f"{LIME_SECONDARY}"),
                Text(f"🌳 Work Tree:     {work_tree}", style=f"{LIME_SECONDARY}"),
                Text(f"🌐 Remote URL:    {remote_url if remote_url else '❌ Non configurato'}", style=f"{LIME_SECONDARY}"),
                Text(""),
                Align.center(Text("🚀 Operazioni da Eseguire", style=f"bold {LIME_ACCENT}")),
                Text(""),
                Text("✅ Creerà un bare repository in Git Directory", style="white"),
                Text("✅ Configurerà il work tree per i dotfiles", style="white"),
                Text("✅ Creerà .gitignore in ~/.config/dotfiles-manager/", style="white"),
                Text("✅ Aggiungerà il remote se configurato", style="white"),
                Text("✅ Creerà comandi per gestire i dotfiles", style="white"),
                Text("✅ Configurerà le impostazioni ottimali", style="white")
            ),
            title="🎨 REPOSITORY INITIALIZATION",
            title_align="center",
            border_style=LIME_PRIMARY,
            padding=(1, 2)
        ))
        
        # Flag per tracciare se abbiamo appena eliminato il repository
        repository_just_deleted = False

        # Check if git directory already exists
        if os.path.exists(git_dir):
            console.print()
            console.print(Panel(
                Group(
                    Align.center(Text("🚨 REPOSITORY ESISTENTE RILEVATO", style="bold red")),
                    Text(""),
                    Align.center(Text(f"📁 {git_dir}", style="bold yellow")),
                    Align.center(Text("esiste già e contiene dati!", style="yellow")),
                    Text(""),
                    Align.center(Text("⚠️  OPERAZIONE DISTRUTTIVA ⚠️", style="bold red")),
                    Text(""),
                    Text("Scegli come procedere:", style=f"bold {LIME_PRIMARY}"),
                    Text(""),
                    Text("🔥 [s] SOSTITUISCI", style="bold red"),
                    Text("   └─ Elimina completamente il repository esistente", style="red"),
                    Text("   └─ Crea un nuovo repository vuoto", style="red"),
                    Text("   └─ TUTTI I DATI ESISTENTI ANDRANNO PERSI!", style="bold red"),
                    Text(""),
                    Text("🛡️  [n] ANNULLA", style="bold green"),
                    Text("   └─ Mantieni il repository esistente", style="green"),
                    Text("   └─ Nessuna modifica verrà effettuata", style="green"),
                    Text("   └─ Opzione sicura - nessun dato perso", style="green"),
                    Text(""),
                    Align.center(Text("⚠️  LA SOSTITUZIONE È IRREVERSIBILE! ⚠️", style="bold red"))
                ),
                title="💥 ATTENZIONE - DATI ESISTENTI",
                title_align="center",
                border_style="red",
                padding=(1, 2)
            ))

            console.print()
            console.print("🎯 Scelta (s/n): ", end="")
            choice = get_key()
            console.print(f"[bold]{choice}[/bold]")

            if choice.lower() == 's':
                # Conferma finale per l'eliminazione con interfaccia più bella
                console.print()
                console.print(Panel(
                    Group(
                        Align.center(Text("💀 CONFERMA ELIMINAZIONE DEFINITIVA 💀", style="bold red")),
                        Text(""),
                        Align.center(Text("Stai per ELIMINARE DEFINITIVAMENTE:", style="red")),
                        Align.center(Text(f"📁 {git_dir}", style="bold yellow")),
                        Text(""),
                        Text("🔥 Questa azione comporta:", style="bold red"),
                        Text("   • Cancellazione COMPLETA del repository", style="red"),
                        Text("   • Perdita di TUTTA la cronologia git", style="red"),
                        Text("   • Eliminazione di TUTTI i commit", style="red"),
                        Text("   • Rimozione di TUTTE le configurazioni", style="red"),
                        Text("   • NESSUN modo per recuperare i dati", style="red"),
                        Text(""),
                        Align.center(Text("⚠️  OPERAZIONE IRREVERSIBILE ⚠️", style="bold red")),
                        Text(""),
                        Align.center(Text("Sei ASSOLUTAMENTE SICURO di voler procedere?", style="bold red"))
                    ),
                    title="🚨 ULTIMA POSSIBILITÀ DI FERMARTI",
                    title_align="center",
                    border_style="red",
                    padding=(1, 2)
                ))

                console.print()
                if not get_confirmation("CONFERMA: Elimina definitivamente tutti i dati?"):
                    show_popup_notification("✅ Operazione annullata - Repository preservato!", 1.0, LIME_PRIMARY)
                    return

                # Eliminazione con feedback visivo
                console.print()
                console.print(f"[red]💥 Eliminazione repository in corso...[/red]")
                try:
                    import shutil
                    shutil.rmtree(git_dir)
                    console.print(f"[red]🗑️  Repository esistente eliminato: {git_dir}[/red]")
                    console.print(f"[{LIME_PRIMARY}]✅ Proceeding direttamente alla creazione del nuovo repository![/]")
                    # Segna che abbiamo eliminato il repository - salteremo la conferma
                    repository_just_deleted = True
                except Exception as e:
                    show_popup_notification(f"❌ Errore eliminazione: {e}", 2.0, "red")
                    return

            else:
                # 'n' o ESC o qualsiasi altro tasto
                show_popup_notification("✅ Operazione annullata - Repository preservato!", 1.0, LIME_PRIMARY)
                return
        
        # Conferma finale per inizializzazione (solo se non abbiamo appena eliminato il repository)
        if not repository_just_deleted:
            console.print()
            console.print(Panel(
                Group(
                    Align.center(Text("🎯 PRONTO PER L'INIZIALIZZAZIONE", style=f"bold {LIME_PRIMARY}")),
                    Text(""),
                    Text("Il sistema creerà un nuovo repository bare per gestire i tuoi dotfiles.", style=f"{LIME_SECONDARY}"),
                    Text("Tutti i passaggi saranno eseguiti automaticamente e in sicurezza.", style=f"{LIME_SECONDARY}"),
                    Text(""),
                    Align.center(Text("Vuoi procedere con l'inizializzazione?", style=f"bold {LIME_ACCENT}"))
                ),
                title="🚀 CONFERMA INIZIALIZZAZIONE",
                title_align="center",
                border_style=LIME_ACCENT,
                padding=(1, 2)
            ))

            console.print()
            if not get_confirmation("Inizializza il repository dotfiles?"):
                show_popup_notification("✅ Inizializzazione annullata", 1.0, LIME_PRIMARY)
                return

        # Inizializzazione con stile e progresso
        console.print()
        if repository_just_deleted:
            console.print(Panel(
                Align.center(Text("🚀 CREAZIONE NUOVO REPOSITORY...", style=f"bold {LIME_PRIMARY}")),
                border_style=LIME_PRIMARY
            ))
        else:
            console.print(Panel(
                Align.center(Text("🚀 INIZIALIZZAZIONE IN CORSO...", style=f"bold {LIME_PRIMARY}")),
                border_style=LIME_PRIMARY
            ))
        
        try:
            # Passo 1: Creazione directory
            console.print(f"[{LIME_ACCENT}]📁 Passo 1/6: Preparazione directory...[/]")
            git_dir_parent = os.path.dirname(git_dir)
            if not os.path.exists(git_dir_parent):
                os.makedirs(git_dir_parent)
                console.print(f"[{LIME_PRIMARY}]  ✅ Creato directory parent: {git_dir_parent}[/]")
            else:
                console.print(f"[{LIME_PRIMARY}]  ✅ Directory parent già esistente[/]")

            # Passo 2: Inizializzazione repository bare
            console.print(f"[{LIME_ACCENT}]🔧 Passo 2/6: Creazione repository bare...[/]")
            result = subprocess.run([
                'git', 'init', '--bare', git_dir
            ], capture_output=True, text=True, check=True)

            console.print(f"[{LIME_PRIMARY}]  ✅ Repository bare creato: {git_dir}[/]")
            
            # Passo 3: Creazione .gitignore management
            console.print(f"[{LIME_ACCENT}]📝 Passo 3/6: Configurazione .gitignore...[/]")
            gitignore_path = self.create_gitignore_management()

            # Passo 4: Configurazione repository
            console.print(f"[{LIME_ACCENT}]⚙️  Passo 4/6: Configurazione repository...[/]")

            # Create git alias command for easier management
            alias_command = f'git --git-dir="{git_dir}" --work-tree="{work_tree}"'

            # Set up initial configuration for bare repository
            config_commands = [
                (['git', '--git-dir', git_dir, 'config', 'status.showUntrackedFiles', 'no'], "Nascondere file non tracciati"),
                (['git', '--git-dir', git_dir, 'config', 'core.worktree', work_tree], "Configurare work tree"),
                (['git', '--git-dir', git_dir, 'config', 'core.excludesfile', gitignore_path], "Configurare .gitignore globale")
            ]

            for cmd, description in config_commands:
                subprocess.run(cmd, check=True, capture_output=True)
                console.print(f"[{LIME_PRIMARY}]  ✅ {description}[/]")

            console.print(f"[{LIME_PRIMARY}]  ✅ Configurazione di base completata[/]")
            
            # Passo 5: Aggiungere remote (se configurato)
            if remote_url:
                console.print(f"[{LIME_ACCENT}]🌐 Passo 5/6: Configurazione remote...[/]")
                try:
                    subprocess.run(
                        ['git', '--git-dir', git_dir, 'remote', 'add', 'origin', remote_url],
                        check=True, capture_output=True
                    )
                    console.print(f"[{LIME_PRIMARY}]  ✅ Remote 'origin' aggiunto: {remote_url}[/]")
                except subprocess.CalledProcessError:
                    console.print(f"[yellow]  ⚠️  Errore nell'aggiungere il remote (potrebbe già esistere)[/yellow]")
            else:
                console.print(f"[{LIME_ACCENT}]🌐 Passo 5/6: Nessun remote configurato - saltato[/]")

            # Passo 6: Finalizzazione
            console.print(f"[{LIME_ACCENT}]🎯 Passo 6/6: Finalizzazione...[/]")
            console.print(f"[{LIME_PRIMARY}]  ✅ Tutte le configurazioni applicate[/]")
            console.print(f"[{LIME_PRIMARY}]  ✅ Repository pronto per l'uso[/]")

            console.print()
            console.print(Panel(
                Group(
                    Align.center(Text("🎉 INIZIALIZZAZIONE COMPLETATA CON SUCCESSO! 🎉", style=f"bold {LIME_PRIMARY}")),
                    Text(""),
                    Text("🚀 Il tuo repository dotfiles è ora configurato e pronto per l'uso!", style=f"{LIME_SECONDARY}"),
                    Text(""),
                    Text("📋 Comandi utili:", style=f"bold {LIME_ACCENT}"),
                    Text(f"   {alias_command} add <file>", style="white"),
                    Text(f"   {alias_command} commit -m \"message\"", style="white"),
                    Text(f"   {alias_command} status", style="white"),
                    Text(f"   {alias_command} log --oneline", style="white"),
                    "" if not remote_url else Text(f"   {alias_command} push origin main", style="white"),
                    Text(""),
                    Text("💡 Suggerimento:", style=f"bold {LIME_ACCENT}"),
                    Text("   Crea un alias per semplificare i comandi:", style=f"{LIME_SECONDARY}"),
                    Text(f"   alias dotfiles='{alias_command}'", style="white"),
                    Text(""),
                    Align.center(Text("Ora puoi iniziare a gestire i tuoi dotfiles! 🌿", style=f"bold {LIME_PRIMARY}"))
                ),
                title="✨ REPOSITORY DOTFILES INIZIALIZZATO",
                title_align="center",
                border_style=LIME_PRIMARY,
                padding=(1, 2)
            ))
            
        except subprocess.CalledProcessError as e:
            console.print()
            console.print(Panel(
                Group(
                    Align.center(Text("❌ ERRORE DURANTE L'INIZIALIZZAZIONE", style="bold red")),
                    Text(""),
                    Text("Si è verificato un errore durante la creazione del repository:", style="red"),
                    Text(f"   {e.stderr.strip() if e.stderr else str(e)}", style="yellow"),
                    Text(""),
                    Text("Possibili cause:", style="red"),
                    Text("• Permessi insufficienti nella directory", style="white"),
                    Text("• Git non installato o non accessibile", style="white"),
                    Text("• Directory non scrivibile", style="white"),
                    Text(""),
                    Text("Verifica la configurazione e riprova.", style=f"{LIME_SECONDARY}")
                ),
                title="🚨 ERRORE INIZIALIZZAZIONE",
                title_align="center",
                border_style="red",
                padding=(1, 2)
            ))

        except Exception as e:
            console.print()
            console.print(Panel(
                Group(
                    Align.center(Text("💥 ERRORE IMPREVISTO", style="bold red")),
                    Text(""),
                    Text("Si è verificato un errore imprevisto:", style="red"),
                    Text(f"   {str(e)}", style="yellow"),
                    Text(""),
                    Text("Si prega di verificare:", style="red"),
                    Text("• La configurazione delle directory", style="white"),
                    Text("• I permessi del filesystem", style="white"),
                    Text("• L'installazione di Git", style="white")
                ),
                title="💀 ERRORE CRITICO",
                title_align="center",
                border_style="red",
                padding=(1, 2)
            ))

        console.print()
        console.print(f"[{LIME_SECONDARY}]Premi un tasto per continuare...[/]")
        get_key()  # Semplice - qualsiasi tasto continua

    def restore_files(self):
        """Menu option 4: Restore files"""
        console.print(Panel(
            Text("🔄 FILE RESTORATION\n\nRestore your dotfiles from backups...",
                 style=LIME_PRIMARY),
            title="Restore Files",
            border_style=LIME_ACCENT
        ))
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press any key to continue (ESC to cancel)...[/]")
        wait_for_key()

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
                choice = self.handle_menu_navigation()

                if choice == 1:
                    console.clear()
                    self.view_modified_files()
                elif choice == 2:
                    console.clear()
                    self.add_remove_files()
                elif choice == 3:
                    console.clear()
                    self.settings()
                elif choice == 4:
                    console.clear()
                    self.restore_files()
                elif choice == 5:
                    self.quit_application()

        except KeyboardInterrupt:
            console.print(f"\n[{LIME_ACCENT}]Interrupted! Goodbye! 👋[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def main():
    """Entry point"""
    # Create and run the dotfiles manager directly
    manager = DotfilesManager()
    manager.run()

if __name__ == "__main__":
    main()
