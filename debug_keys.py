#!/usr/bin/env python3
"""
Debug key detection - show exactly what codes are received
"""

import os
import sys
import termios
import tty
import select

# Key codes constants
class KeyCodes:
    ESC = '\x1b'
    ENTER = '\r'
    ARROW_UP = '\x1b[A'
    ARROW_DOWN = '\x1b[B'
    ARROW_RIGHT = '\x1b[C'
    ARROW_LEFT = '\x1b[D'

def debug_key():
    """Debug version - shows raw codes"""
    if not sys.stdin.isatty():
        print("Non-interactive terminal")
        return 'q'

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)

        # Handle ESC key
        if key == KeyCodes.ESC:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                try:
                    next_chars = sys.stdin.read(2)
                    if len(next_chars) >= 2 and next_chars[0] == '[':
                        key = KeyCodes.ESC + next_chars
                    else:
                        key = KeyCodes.ESC
                except:
                    key = KeyCodes.ESC

        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    print("🔍 DEBUG: Press arrow keys to see raw codes")
    print("Expected codes:")
    print(f"  UP:    {repr(KeyCodes.ARROW_UP)}")
    print(f"  DOWN:  {repr(KeyCodes.ARROW_DOWN)}")
    print(f"  LEFT:  {repr(KeyCodes.ARROW_LEFT)}")
    print(f"  RIGHT: {repr(KeyCodes.ARROW_RIGHT)}")
    print(f"  ESC:   {repr(KeyCodes.ESC)}")
    print("Press 'q' to quit")
    print("-" * 50)

    while True:
        print("Press key: ", end="", flush=True)
        key = debug_key()

        print(f"Raw code: {repr(key)}")

        # Test comparisons
        if key == KeyCodes.ARROW_UP:
            print("  ✅ Matches ARROW_UP")
        elif key == KeyCodes.ARROW_DOWN:
            print("  ✅ Matches ARROW_DOWN")
        elif key == KeyCodes.ARROW_LEFT:
            print("  ✅ Matches ARROW_LEFT")
        elif key == KeyCodes.ARROW_RIGHT:
            print("  ✅ Matches ARROW_RIGHT")
        elif key == KeyCodes.ESC:
            print("  ✅ Matches standalone ESC")
        elif key.lower() == 'q':
            print("  ✅ Quit detected")
            break
        else:
            print(f"  ❌ No match found")
            print(f"      Length: {len(key)}")
            if len(key) > 1:
                for i, char in enumerate(key):
                    print(f"      [{i}]: {repr(char)} (ord: {ord(char)})")
        print()

if __name__ == "__main__":
    main()