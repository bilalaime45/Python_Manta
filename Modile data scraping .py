import uiautomator2 as u2
import os
import time
import re
import subprocess



d = u2.connect()
print(d.info)
print(d.dump_hierarchy())

subprocess.run(["adb", "shell", "cmd", "notification", "set_dnd", "on"])

time.sleep(2)

subprocess.run(["adb", "shell", "cmd", "notification", "set_dnd", "off"])
    
d.app_start("com.daraz.android")  # replace with your actual package name
time.sleep(3)
print(d.app_current())

d(resourceId="com.daraz.android:id/srp_search_input_box").click()
time.sleep(1)
d.send_keys("shoes")
d.press("enter")   # or find/tap the actual search button if enter doesn't trigger it
time.sleep(3)

all_products = []
seen_titles = set()
no_new_count = 0

def safe_dump():
    current = d.app_current()
    if current['package'] != 'com.daraz.android':
        time.sleep(1)  # wait a moment for overlay to clear
        current = d.app_current()
    if current['package'] != 'com.daraz.android':
        return None  # still not on Daraz, skip this cycle
    return d.dump_hierarchy()

def robust_dump():
    retries=3
    delay=1
    for _ in range(retries):
        xml = safe_dump()
        if 'com.daraz.android' in xml:
            return xml
        time.sleep(delay)
    return xml  # return last attempt even if imperfect

def extract_products(xml):
    texts = re.findall(r'text="([^"]*)"', xml)
    texts = [t.replace('&#10;', ' ').strip() for t in texts if t.strip()]
    products = []
    i = 0
    while i < len(texts):
        if texts[i].startswith('#') or len(texts[i].split()) > 3:
            if i + 2 < len(texts) and texts[i+1].strip() == 'Rs.':
                products.append({'title': texts[i], 'price': f"Rs. {texts[i+2]}"})
                i += 3
                continue
        i += 1
    return products

while no_new_count < 3:   # stop after 3 scrolls with nothing new
    xml = robust_dump()
    new_products = extract_products(xml)
    added = 0
    for p in new_products:
        if p['title'] not in seen_titles:
            seen_titles.add(p['title'])
            all_products.append(p)
            added += 1
    if added == 0:
        no_new_count += 1
    else:
        no_new_count = 0
    d.swipe_ext("up", scale=0.8)   # scroll down the list
    time.sleep(1.5)

print(f"Collected {len(all_products)} products")

for p in all_products:
    print(p)

___________________________________________________________________________________________

output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(output_dir, "hierarchy.xml")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(d.dump_hierarchy())
    


