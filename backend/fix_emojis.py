import re

path = 'api/v1/endpoints/chat.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'print(' in line:
        # Just encode to ascii and ignore errors, then decode back.
        # This will strip all emojis from print lines!
        # Note: We must not strip non-ascii from Python code (like comments), but only if it's safe. 
        # But wait, stripping all non-ascii from print statements is totally fine.
        
        # Actually, let's just replace the specific known emoji sequences:
        # \u2705 ✅, \u26a0 ⚠️, \ufe0f (variation selector), \U0001f9e0 🧠, \U0001f4c1 📁, \U0001f4bb 💻, \U0001f504 🔄
        # And literal emojis in the code like "⚠️" or "✅"
        clean_line = line.encode('ascii', 'ignore').decode('ascii')
        new_lines.append(clean_line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Emjois stripped from print statements.")
