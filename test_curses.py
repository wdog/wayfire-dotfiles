#!/usr/bin/env python3

import curses
from config_manager import ConfigManager
from pathlib import Path

def test_input_dialog(stdscr):
    """Test the input dialog function"""
    curses.curs_set(0)
    
    # Initialize colors
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    
    # Simple test screen
    stdscr.clear()
    stdscr.addstr(0, 0, "Curses Test - Press any key to start input dialog, 'q' to quit")
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        else:
            # Test input dialog
            try:
                result = simple_input_dialog(stdscr, "Test Input", "Enter something:", "default")
                stdscr.clear()
                stdscr.addstr(0, 0, f"You entered: '{result}'")
                stdscr.addstr(1, 0, "Press any key to test again, 'q' to quit")
                stdscr.refresh()
            except Exception as e:
                stdscr.clear()
                stdscr.addstr(0, 0, f"Error: {e}")
                stdscr.addstr(1, 0, "Press any key to continue")
                stdscr.refresh()

def simple_input_dialog(stdscr, title, prompt, default=""):
    """Simplified input dialog for testing"""
    height, width = stdscr.getmaxyx()
    
    # Create dialog
    dialog_height = 7
    dialog_width = min(50, width - 4)
    start_y = (height - dialog_height) // 2
    start_x = (width - dialog_width) // 2
    
    dialog = curses.newwin(dialog_height, dialog_width, start_y, start_x)
    dialog.box()
    dialog.addstr(0, 2, f" {title} ")
    
    # Add prompt safely
    prompt_text = prompt[:dialog_width-6]
    dialog.addstr(2, 2, prompt_text)
    
    # Input area
    input_y = start_y + 4
    input_x = start_x + 2
    input_width = dialog_width - 4
    
    input_win = curses.newwin(1, input_width, input_y, input_x)
    
    # Initialize with default
    result = default[:input_width-2]
    
    dialog.refresh()
    
    while True:
        # Display current input
        input_win.clear()
        display_text = result[:input_width-2]
        input_win.addstr(0, 0, display_text)
        input_win.refresh()
        
        key = input_win.getch()
        
        if key == ord('\n') or key == 10:  # Enter
            break
        elif key == 27:  # Escape
            result = default
            break
        elif key == curses.KEY_BACKSPACE or key == 127:
            if result:
                result = result[:-1]
        elif 32 <= key <= 126 and len(result) < input_width-3:
            result += chr(key)
    
    dialog.clear()
    dialog.refresh()
    return result

if __name__ == "__main__":
    try:
        curses.wrapper(test_input_dialog)
        print("Curses test completed successfully")
    except Exception as e:
        print(f"Curses test failed: {e}")