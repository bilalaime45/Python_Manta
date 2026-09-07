from curl_cffi import requests
from bs4 import BeautifulSoup
import json

url = "https://www.walmart.com/cp/new-arrivals/2593086"
response = requests.get(url, impersonate="chrome", timeout=30)
print(response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
script_tag = soup.find("script", id="__NEXT_DATA__")


data = json.loads(script_tag.string)

modules = (data.get("props", {}).get("pageProps", {}).get("initialTempoData", {}).get("pageMetadata", {}).get("contentLayout", {}).get("modules", []))

all_products = []

for module in modules:
    configs = module.get("configs", {})
    print(configs)
    products_config = configs.get("productsConfig", {})
    print(products_config)
    if products_config.get("products"):
        all_products.extend(products_config["products"])
        print(all_products)
            
    item_stacks = configs.get("itemStacks",{}).get("itemStacks", [])
    for stack in item_stacks:
        if stack.get("items"):
            all_products.extend(stack["items"])
            
            
print(f"Total products found: {len(all_products)}")

   
    results = []
    for p in all_products:
        item_id = p.get("usItemId")
        href = p.get("canonicalUrl")
        if item_id and href:
            full_url = "https://www.walmart.com" + href if href.startswith("/") else href
            results.append({"item_id": item_id, "href": full_url})

    for r in results[:10]:
        print(r)

    # Check for your target item
    target_id = "19558774978"
    found = any(r["item_id"] == target_id for r in results)
    print(f"\nTarget item {target_id} found: {found}")