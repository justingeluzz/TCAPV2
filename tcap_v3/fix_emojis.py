#!/usr/bin/env python3
"""
Script to remove emojis from logging statements to fix Windows terminal encoding issues
"""

import os
import re
import glob

def remove_emojis_from_file(file_path):
    """Remove emojis from logging statements in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match emoji characters in logger.info statements
    emoji_pattern = r'(self\.logger\.info\([^"]*["\'])([^"\']*?)([STARTPROFITEXECSCANUPSTATSSUCCESSTARGETGUARDSTOP⏸▶⌨DOWNSTARTARGETSTATSUPDOWNSTATSSCANSCANSTATSUPDOWNSTATS]+)([^"\']*?)(["\'])',
    
    # More specific pattern for our use case
    pattern = r'(self\.logger\.info\([^"]*["\'])([STARTPROFITEXECSCANUPSTATSSUCCESSTARGETGUARDSTOP⏸▶⌨DOWNSTAR]+\s*)'
    
    def replace_emoji(match):
        prefix = match.group(1)
        emoji_part = match.group(2)
        # Remove emojis and any trailing space
        return prefix
    
    # Replace emojis in logger.info statements
    new_content = re.sub(pattern, replace_emoji, content)
    
    # Write back only if content changed
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"SUCCESS: Fixed emojis in {file_path}")
        return True
    return False

def main():
    """Main function to process all Python files"""
    # Get all Python files in the current directory
    python_files = glob.glob("*.py")
    
    fixed_count = 0
    for file_path in python_files:
        if remove_emojis_from_file(file_path):
            fixed_count += 1
    
    print(f"\nSTATS: Summary: Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
