#!/usr/bin/env python3
"""
Wayfire Dotfiles Manager
A beautiful TUI tool for managing dotfiles with Rich library
"""

import os
import sys
import termios
import tty
from rich.console import Console
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

    def add_remove_files(self):
        """Menu option 2: Add/Remove files"""
        console.print(Panel(
            Text("➕ FILE MANAGEMENT\n\nThis feature will help you add/remove tracked files...",
                 style=LIME_PRIMARY),
            title="Add/Remove Files",
            border_style=LIME_ACCENT
        ))
        console.print(f"[{LIME_SECONDARY}]Feature coming soon! Press Enter to continue...[/]")
        input()

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
