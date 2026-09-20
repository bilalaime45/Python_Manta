import requests
import re
import json
import os
from bs4 import BeautifulSoup
import time


url = "https://www.walmart.com/cp/new-arrivals/2593086"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
r = requests.get(url, headers=headers, timeout=10)
    
def fetch_with_retry(url, headers, max_retries=3, delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            return r
        except requests.exceptions.ConnectionError as e:
            print(f"Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Giving up.")
                return None
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt}/{max_retries} timed out")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                return None

match = re.search(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    r.text, re.DOTALL
)
data_arrival = json.loads(match.group(1))

# Recursively walk the whole data tree looking for brand + canonicalUrl pairs
results2 = []
found_specs = []

def walk_arrival(obj):
    if isinstance(obj, dict):
        if "brand" in obj and "canonicalUrl" in obj:
            results2.append({"brand": obj["brand"], "canonicalUrl": obj["canonicalUrl"]})
        for v in obj.values():
            walk_arrival(v)
    elif isinstance(obj, list):
        for item in obj:
            walk_arrival(item)


def walk(obj):
    if isinstance(obj, dict):
        if "specifications" in obj and isinstance(obj["specifications"], list):
            found_specs.append(obj["specifications"])
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            walk(item)

def price_features_specs(r):
    soup = BeautifulSoup(r.text, "html.parser")
    # --- Price ---
    price_tag = soup.select_one('span[itemprop="price"]')
    price = price_tag.get_text(strip=True) if price_tag else None
    print("Price:", price)
    # --- Features list ---
    features_ul = soup.select_one("ul.mv0.pl4")
    features = {}
    if features_ul:
        for li in features_ul.find_all("li"):
            text = li.get_text(strip=True)
            if ":" in text:
                key, value = text.split(":", 1)
                features[key.strip()] = value.strip()
            else:
                features[text] = None
    print("Features:")
    for k, v in features.items():
        print(f"  {k}: {v}")
    # --- Specs list ---
    match = re.search(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    r.text, re.DOTALL
)
    data = json.loads(match.group(1))
    #Recursively find the "specifications" list wherever it lives in the tree
    walk(data)
    if found_specs:
        specs_list = found_specs[0] # take the first match found
        specs = {item["name"]: item["value"] for item in specs_list if "name" in item and "value" in item}
        print(f"Found {len(specs)} specs\n")
        for k, v in specs.items():
            print(f"{k}: {v}")
    else:
        print("No 'specifications' key found in JSON")
    



walk_arrival(data_arrival)

print(f"Found {len(results2)} brand/canonicalUrl pairs\n")
for r in results2:
    print("Processsing url:", "https://www.walmart.com"+r['canonicalUrl'])
    time.sleep(2)
    page_html=fetch_with_retry("https://www.walmart.com"+r['canonicalUrl'],headers)
    if page_html is not None:
        print("Success:", page_html.status_code)
        price_features_specs(page_html)
    else:
        print("Failed to fetch after retries")
    
    
 