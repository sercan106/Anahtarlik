
import os

file_path = r"c:\Users\user\Desktop\YAZILIM\Anahtarlık\courseapp\anahtarlik\templates\anahtarlik\ev.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_string = """            <p>{{ ayarlar.hizmetler_aciklama|default:"Evcil dostlarınız için en iyi dijital kimlik ve sağlık takip
                çözümleri" }}</p>"""

new_string = """            <p>{{ ayarlar.hizmetler_aciklama|default:"Evcil dostlarınız için en iyi dijital kimlik ve sağlık takip çözümleri" }}</p>"""

if old_string in content:
    print("Found the string. Replacing...")
    new_content = content.replace(old_string, new_string)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced successfully.")
else:
    print("String not found. Dumping a snippet to debug:")
    start_index = content.find("ayarlar.hizmetler_aciklama")
    if start_index != -1:
        print(repr(content[start_index-20:start_index+150]))
    else:
        print("Could not find the target area at all.")
