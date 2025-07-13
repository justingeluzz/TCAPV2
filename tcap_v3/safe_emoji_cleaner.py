#!/usr/bin/env python3
"""
Safe Emoji Removal Script for TCAP v3
Removes all Unicode emojis without corrupting files
"""

import os
import re
from pathlib import Path

def remove_emojis_from_file(file_path):
    """Remove all emojis from a Python file safely"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Original content for comparison
        original_content = content
        
        # Define emoji replacements
        emoji_replacements = {
            # Error emojis
            '❌ ': 'ERROR: ',
            '❌': 'ERROR',
            
            # Warning emojis
            '⚠️ ': 'WARNING: ',
            '⚠️': 'WARNING',
            
            # Success emojis
            '✅ ': 'SUCCESS: ',
            '✅': 'SUCCESS',
            
            # Action emojis
            '🚀 ': 'START: ',
            '🚀': 'START',
            '🎯 ': 'TARGET: ',
            '🎯': 'TARGET',
            '🔍 ': 'SCAN: ',
            '🔍': 'SCAN',
            '⚡ ': 'EXEC: ',
            '⚡': 'EXEC',
            '🛡️ ': 'GUARD: ',
            '🛡️': 'GUARD',
            '💰 ': 'PROFIT: ',
            '💰': 'PROFIT',
            '⏹️ ': 'STOP: ',
            '⏹️': 'STOP',
            
            # Info emojis
            '📊 ': 'STATS: ',
            '📊': 'STATS',
            '📈 ': 'UP: ',
            '📈': 'UP',
            '📉 ': 'DOWN: ',
            '📉': 'DOWN',
            '🚨 ': 'ALERT: ',
            '🚨': 'ALERT',
            
            # Other emojis
            '⭐ ': 'STAR: ',
            '⭐': 'STAR',
            '🔥 ': 'HOT: ',
            '🔥': 'HOT',
        }
        
        # Apply replacements
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Remove any remaining Unicode emojis using regex
        # This pattern matches most Unicode emoji ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002600-\U000027BF"  # miscellaneous symbols
            "\U0001f926-\U0001f937"  # supplemental symbols
            "\U00010000-\U0010ffff"  # other unicode ranges
            "\u2640-\u2642"          # gender symbols
            "\u2600-\u2B55"          # misc symbols
            "\u200d"                 # zero width joiner
            "\u23cf"                 # eject symbol
            "\u23e9"                 # fast forward
            "\u231a"                 # watch
            "\ufe0f"                 # variation selector
            "\u3030"                 # wavy dash
            "]+", flags=re.UNICODE)
        
        content = emoji_pattern.sub('', content)
        
        # Write back to file if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"SUCCESS: Cleaned emojis from {file_path}")
            return True
        else:
            print(f"INFO: No emojis found in {file_path}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to process {file_path}: {e}")
        return False

def main():
    """Remove emojis from all Python files in TCAP v3"""
    tcap_dir = Path(".")
    python_files = list(tcap_dir.glob("*.py"))
    
    print("TCAP v3 Emoji Removal Tool")
    print("=" * 50)
    
    cleaned_count = 0
    for py_file in python_files:
        if py_file.name != "safe_emoji_cleaner.py":  # Don't process this script
            if remove_emojis_from_file(py_file):
                cleaned_count += 1
    
    print("=" * 50)
    print(f"SUCCESS: Cleaned {cleaned_count} files")
    print("All files are now safe for Windows cp1252 encoding!")

if __name__ == "__main__":
    main()
