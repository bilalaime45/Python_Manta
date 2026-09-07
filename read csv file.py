import os
import csv

output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(output_dir, "links.csv")

companies_dict = {}

with open(file_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['name']
        full_url = row['url']
        companies_dict[full_url] = {"name": name, "url": full_url}
        
        
        
        
        
        
        
  
# -------------This code resolve the skipping URL--------------------------------------------

     
     
result_queue = Queue()
dict_lock = threading.Lock()

def safe_open(sb, url, timeout=20):
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


def restart_browser(sb=None):
    """Quits old browser (if any) and starts a fresh, verified session."""
    if sb:
        try:
            sb.driver.quit()
        except Exception:
            pass
    sb = sb_cdp.Chrome(guest=True)
    sb.open("https://www.manta.com/")
    sb.sleep(30)
    sb.solve_captcha()
    sb.wait_for_element_absent("input[disabled]")
    sb.sleep(30)
    return sb


def worker_batch(url_list, result_queue):
    """Each thread processes a list of URLs using its own browser instance."""
    sb = restart_browser()
    for url in url_list:
        MAX_BROWSER_RESTARTS = 3  
        browser_restart_count = 0
        url_processed = False
        while not url_processed and browser_restart_count <= MAX_BROWSER_RESTARTS:
            try:
                success = safe_open(sb, url, timeout=30)
                if not success:
                    print(f"Timeout loading {url} — restarting browser (attempt {browser_restart_count + 1})")
                    sb = restart_browser(sb)
                    browser_restart_count += 1
                    continue  
                sb.sleep(5)
                title = sb.get_title()
                retry_count = 0
                max_retries = 6
                while title == "Just a moment..." and retry_count < max_retries:
                    print(f"Cloudflare challenge detected on {url}, waiting 10s (attempt {retry_count + 1})")
                    ok = safe_open(sb, url, timeout=25)
                    if not ok:
                        break
                    sb.sleep(10)
                    title = sb.get_title()
                    retry_count += 1
                if title == "Just a moment...":
                    print(f"Still blocked after {max_retries} retries on {url} — restarting browser (attempt {browser_restart_count + 1})")
                    sb = restart_browser(sb)
                    browser_restart_count += 1
                    continue  
                html = sb.get_page_source()
                soup = BeautifulSoup(html, "html.parser")
                info = extract_company_info(soup)
                result_queue.put((url, clean_company(info)))
                url_processed = True  
            except Exception as e:
                print(f"Failed: {url} - {e}")
                url_processed = True 
        if not url_processed:
            print(f" Giving up on {url} after {MAX_BROWSER_RESTARTS} browser restarts")
    sb.driver.quit()


NUM_WORKERS = 5
all_urls = list(companies_dict.keys())[3000:4000]
backup_companies_dict = companies_dict
chunk_size = len(all_urls) // NUM_WORKERS + 1
url_chunks = [all_urls[i:i + chunk_size] for i in range(0, len(all_urls), chunk_size)]

threads = []
start_time = time.time()

for i, chunk in enumerate(url_chunks):
    t = threading.Thread(target=worker_batch, args=(chunk, result_queue), daemon=True)
    threads.append(t)
    t.start()
    print(f"Started worker {i+1}/{len(url_chunks)}")
    if i < len(url_chunks) - 1:
        time.sleep(3)

try:
    while any(t.is_alive() for t in threads):
        time.sleep(2)
except KeyboardInterrupt:
    print("\nInterrupted by user — main threads are daemons, exiting now")

elapsed = time.time() - start_time
print(f"\nTotal time: {elapsed:.1f} seconds")