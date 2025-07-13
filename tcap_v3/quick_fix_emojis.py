#!/usr/bin/env python3
"""
Quick fix to remove all emojis from main_engine.py
"""

import re

def fix_main_engine():
    """Remove all emojis from main_engine.py"""
    file_path = "main_engine.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Dictionary of emoji replacements for logging messages
    emoji_replacements = {
        '⏸ ': '',
        '▶ ': '',
        'SUCCESS: ': '',
        'WARNING: ': 'WARNING: ',
        'EXEC: ': '',
        'GUARD: ': '',
        'TARGET: ': '',
        'ALERT: ': 'ALERT: ',
        'STATS: ': '',
        '⌨ ': '',
    }
    
    # Apply replacements
    for emoji, replacement in emoji_replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"SUCCESS: Fixed emojis in {file_path}")

if __name__ == "__main__":
    fix_main_engine()
