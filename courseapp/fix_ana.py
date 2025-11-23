
import os

file_path = r"c:\Users\user\Desktop\YAZILIM\Anahtarlık\courseapp\templates\ana.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for the space version just in case
if "evcil hayvanlar" in content:
    print("Found 'evcil hayvanlar' with space! Fixing...")
    content = content.replace("evcil hayvanlar", "evcil_hayvanlar")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed space issue.")
else:
    print("Did not find 'evcil hayvanlar' with space.")

# Check if the underscore version is there
if "evcil_hayvanlar" in content:
    print("Found 'evcil_hayvanlar' (correct).")
else:
    print("Did not find 'evcil_hayvanlar' either!")
