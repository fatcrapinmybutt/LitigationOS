"""Strip all non-ASCII emoji from cortex_build.py and cortex_app.py, 
replacing them with ASCII-safe equivalents."""
import re

files_to_fix = [
    r"J:\CORTEX\cortex_build.py",
    r"J:\CORTEX\cortex_app.py",
]

# Map common emoji to ASCII replacements
EMOJI_MAP = {
    '📦': '[PKG]',
    '📊': '[+]',
    '📝': '[+]',
    '🚀': '[+]',
    '🎯': '[>]',
    '✅': '[OK]',
    '❌': '[ERR]',
    '🔨': '[BUILD]',
    '🖥': '[DESKTOP]',
    '🌐': '[WEB]',
    '✋': '[STOP]',
    '🧠': '[BRAIN]',
    '📄': '[FILE]',
    '1️⃣': '[1]',
    '2️⃣': '[2]',
    '3️⃣': '[3]',
    '4️⃣': '[4]',
}

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply known mappings
    for emoji, replacement in EMOJI_MAP.items():
        content = content.replace(emoji, replacement)
    
    # Strip any remaining non-ASCII non-standard chars in print statements
    # Find any remaining chars > U+007F that aren't in normal text
    remaining_emoji = set()
    for ch in content:
        if ord(ch) > 0x7F and ord(ch) > 0x024F:  # Beyond Latin Extended
            remaining_emoji.add(ch)
    
    for ch in remaining_emoji:
        content = content.replace(ch, '[*]')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        # Show what changed
        removed = set(original) - set(content)
        if removed:
            print(f"  Removed chars: {removed}")
    else:
        print(f"No changes: {filepath}")

print("\nDone!")
