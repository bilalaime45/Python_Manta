import requests
import re
import json
import os

url = "https://www.walmart.com/cp/new-arrivals/2593086"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
r = requests.get(url, headers=headers, timeout=10)

match = re.search(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    r.text, re.DOTALL
)
data = json.loads(match.group(1))

# Explore the props tree
props = data["props"]
print("props keys:", list(props.keys()))

page_props = props.get("pageProps", {})
print("\npageProps keys:", list(page_props.keys()))

# Walmart often nests actual product/page data under something like 
# 'initialData' or similar inside pageProps — print a level deeper
for k, v in page_props.items():
    if isinstance(v, dict):
        print(f"\n{k} -> keys: {list(v.keys())[:15]}")
    elif isinstance(v, list):
        print(f"\n{k} -> list of {len(v)} items")
    else:
        print(f"\n{k} -> {type(v).__name__}: {str(v)[:100]}")

# Save the whole thing so you can browse it in an editor

output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
os.makedirs(output_dir, exist_ok=True)  # creates the folder if missing, does nothing if it exists
output_path = os.path.join(output_dir, "Json_file.json")
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)
    
    
    
________________________________________________________________________________

import requests
import re
import json

url = "https://www.walmart.com/cp/new-arrivals/2593086"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
r = requests.get(url, headers=headers, timeout=10)

match = re.search(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    r.text, re.DOTALL
)
data = json.loads(match.group(1))

# Recursively walk the whole data tree looking for brand + canonicalUrl pairs
results = []

def walk(obj):
    if isinstance(obj, dict):
        if "brand" in obj and "canonicalUrl" in obj:
            results.append({"brand": obj["brand"], "canonicalUrl": obj["canonicalUrl"]})
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            walk(item)

walk(data)

print(f"Found {len(results)} brand/canonicalUrl pairs\n")
for r in results:
    print(r)



# Optionally save to a file
with open("brands_and_urls.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} entries to brands_and_urls.json")
