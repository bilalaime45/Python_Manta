
# -------------Run this Scraper in US time Zones in Pakistani Time 6:00 PM to 2:00 AM--------------------------------------------

import json
import time
import threading
import concurrent.futures
from queue import Queue
from seleniumbase import sb_cdp
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import csv
import re
from urllib.parse import urlparse, parse_qs, unquote
from email_validator import validate_email, EmailNotValidError
import os

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False
        

def extract_company_info(soup):
    data = {"phone": None, "address": None, "website": None, "email": None, "scope": []}
    contact_section = soup.find("div", id="contactContent")
    if contact_section:
        address_div = contact_section.find("div", class_=lambda c: c and all(cls in c.split() for cls in ["lg:w-3/5", "mr-2", "mb-2", "lg:mb-2"]))
        if address_div:
            ul = address_div.find("ul", class_="text-gray-800")
            if ul:
                lis = ul.find_all("li")
                parts = [li.get_text(" ", strip=True) for li in lis]
                data["address"] = ", ".join(p for p in parts if p)
        info_div = contact_section.find("div", class_=lambda c: c and "lg:w-2/5" in c.split())
        if info_div:
            for li in info_div.find_all("li"):
                a_tag = li.find("a", href=True)
                if not a_tag:
                    continue
                href = a_tag["href"].strip()
                if href.startswith("tel:"):
                    data["phone"] = a_tag.get_text(strip=True)
                elif href.startswith("mailto:"):
                    candidate_email = href.replace("mailto:", "").strip()
                    data["email"] = candidate_email if is_valid_email(candidate_email) else None
                elif "urlverify" in href:
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    data["website"] = unquote(qs["redirect"][0]) if "redirect" in qs else href
    services_section = soup.find("div", id="servicesContent")
    if services_section:
        scope_divs = services_section.find_all("div", class_=lambda c: c and all(cls in c.split() for cls in ["truncate", "pr-4"]))
        data["scope"] = [d.get_text(strip=True) for d in scope_divs]
    return data


BASE_URL = "https://www.manta.com"

def clean_company(company):
    cleaned = {}
    for key, value in company.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        cleaned[key] = value
    return cleaned
    
    

sb = sb_cdp.Chrome(guest=True)
endpoint_url = sb.get_endpoint_url()
sb.open("https://www.manta.com/")
sb.sleep(10)
sb.solve_captcha()
sb.wait_for_element_absent("input[disabled]")
sb.sleep(10)

with sync_playwright() as p:             
    browser = p.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://www.manta.com/")
    sb.sleep(10)
    sb.solve_captcha()
    sb.wait_for_element_absent("input[disabled]")
    sb.sleep(10)
                
sb.open("https://www.manta.com/mb_33_E0_000/construction")

import time

MAX_SCROLLS = 3000
STABLE_ROUNDS_NEEDED = 3
TARGET_COMPANIES = 3000
stable_count = 0
new_count=0
last_count = 0
scroll_count = 0
print(f"Starting count: {last_count}")

while scroll_count < MAX_SCROLLS:
    scroll_count += 1
    # Scroll down by a fixed pixel amount instead of jumping to bottom
    sb.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
    sb.sleep(2)  # give server time to load more listings
    new_count += 1 
    print(f"Scroll {scroll_count}: listings = {new_count}")
    if new_count >= TARGET_COMPANIES:
        print(f"Reached target of {TARGET_COMPANIES} companies")
        break
    if new_count == last_count:
        stable_count += 1
        if stable_count >= STABLE_ROUNDS_NEEDED:
            print("No new listings loading — stopping")
            break
    else:
        stable_count = 0
        last_count = new_count

print(f"Finished with {last_count} listings after {scroll_count} scrolls")






html = sb.get_page_source()
soup_const = BeautifulSoup(html, "html.parser")
listings = soup_const.select("div.flex")

companies_dict = {}

for item in listings:
    profile_link = item.select_one("a[href*='/c/']")
    if profile_link is None:
        continue
    href = profile_link.get("href")
    name = profile_link.get_text(strip=True)
    if not href or not name:
        continue
    full_url = urljoin(BASE_URL, href)
    if full_url not in companies_dict:
        companies_dict[full_url] = {"name": name, "url": full_url}

sb.driver.quit()

result_queue = Queue()
dict_lock = threading.Lock()  # protects companies_dict during concurrent updates

def safe_open(sb, url, timeout=20):
    """Runs sb.open() with a hard timeout. Returns True if it succeeded, False if it timed out."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(sb.open, url)
        try:
            future.result(timeout=timeout)
            return True
        except concurrent.futures.TimeoutError:
            return False
        except Exception as e:
            print(f"safe_open error: {e}")
            return False


def worker_batch(url_list, result_queue):
    """Each thread processes a list of URLs using its own browser instance."""
    sb = sb_cdp.Chrome(guest=True)
    sb.open("https://www.manta.com/")
    sb.sleep(30)
    sb.solve_captcha()
    sb.wait_for_element_absent("input[disabled]")
    sb.sleep(30)
    for url in url_list:
        try:
            success = safe_open(sb, url, timeout=30)  # hard cap: never wait more than 25s
            if not success:
                print(f"Timeout loading {url} — restarting browser and skipping this URL")
                try:
                    sb.driver.quit()
                except Exception:
                    pass
                sb = sb_cdp.Chrome(guest=True)  # fresh browser instance
                sb.open("https://www.manta.com/")
                sb.sleep(30)
                sb.solve_captcha()
                sb.wait_for_element_absent("input[disabled]")
                sb.sleep(30)
                continue  # move to next URL, don't process this failed one
            sb.sleep(5)
            title = sb.get_title()
            retry_count = 0
            max_retries = 6
            while title == "Just a moment..." and retry_count < max_retries:
                print(f"Cloudflare challenge detected on {url}, waiting 10s (attempt {retry_count + 1})")
                success = safe_open(sb, url, timeout=25)
                if not success:
                    break
                sb.sleep(10)
                title = sb.get_title()
                retry_count += 1
            if title == "Just a moment...":
                print(f"Still blocked after {max_retries} retries: {url}")
                continue
            html = sb.get_page_source()
            soup = BeautifulSoup(html, "html.parser")
            info = extract_company_info(soup)
            result_queue.put((url, clean_company(info)))
        except Exception as e:
            print(f"Failed: {url} - {e}")
    sb.driver.quit()


result_queue = Queue()
NUM_WORKERS = 5
all_urls = list(companies_dict.keys())[3000:5800]
backup_companies_dict = companies_dict
chunk_size = len(all_urls) // NUM_WORKERS + 1
url_chunks = [all_urls[i:i + chunk_size] for i in range(0, len(all_urls), chunk_size)]
threads = []
start_time = time.time()

for i, chunk in enumerate(url_chunks):
    t = threading.Thread(target=worker_batch, args=(chunk, result_queue), daemon=True)  # daemon=True
    threads.append(t)
    t.start()
    print(f"Started worker {i+1}/{len(url_chunks)}")
    if i < len(url_chunks) - 1:
        time.sleep(3)

# Poll threads with a timeout instead of blocking .join() forever
try:
    while any(t.is_alive() for t in threads):
        time.sleep(2)
except KeyboardInterrupt:
    print("\nInterrupted by user — main threads are daemons, exiting now")

elapsed = time.time() - start_time
print(f"\nTotal time: {elapsed:.1f} seconds")

saved_values = list(result_queue.queue)
while not result_queue.empty():
    url, info = result_queue.get()
    if info is not None and all(info.values()):
        with dict_lock:
            companies_dict[url].update(info)
            companies_dict[url] = clean_company(companies_dict[url])
            print(f"Done: {url}")



required_fields = ['name', 'url', 'phone', 'address', 'website', 'email', 'scope']

incomplete_companies = {}

for url, data in companies_dict.items():
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        incomplete_companies[url] = {'data': data, 'missing': missing_fields}

print(f"Found {len(incomplete_companies)} incomplete companies out of {len(companies_dict)}")



companies_dict = {
    url: info
    for url, info in companies_dict.items()
    if info and all(field in info and info[field] for field in required_fields)
}

final_companies = list(companies_dict.values())



output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
os.makedirs(output_dir, exist_ok=True)  # creates the folder if missing, does nothing if it exists
output_path = os.path.join(output_dir, "with_Email_companies_1000_to_2000.csv")


with open(output_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["name", "url", "phone", "address", "website", "email", "scope"]
    writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
    writer.writeheader()
    for c in final_companies:
        row = c.copy()
        scope_val = row.get("scope", "")
        row["scope"] = "; ".join(scope_val) if isinstance(scope_val, list) else (scope_val or "")
        writer.writerow(row)





output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "Out_Email_companies_1000_to_2000.csv")

with open(output_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["name", "url", "phone", "address", "website", "email", "scope"]
    writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
    writer.writeheader()
    for entry in incomplete_companies.values():
        row = entry["data"].copy()
        scope_val = row.get("scope", "")
        row["scope"] = "; ".join(scope_val) if isinstance(scope_val, list) else (scope_val or "")
        writer.writerow(row)
      
        
        
        
        
        
