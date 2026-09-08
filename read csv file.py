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
        
        
        
        
        
        
        
  
# -------------This code resolve the skipping URL but some times stuck due to bot verification--------------------------------------------

     
     
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
    sb.sleep(50)
    sb.solve_captcha()
    sb.wait_for_element_absent("input[disabled]")
    sb.sleep(10)
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


NUM_WORKERS = 3
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





#--------------------------------------------Run this code in chrome with guest mode False-----------------------------------------------------------




result_queue = Queue()
tab_lock = threading.Lock()  


def safe_open(sb, url, timeout=10):
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


def worker_batch(sb, tab_id, url_list, result_queue, worker_id):
    for url in url_list:
        MAX_RETRIES = 3
        retry_count = 0
        url_processed = False
        while not url_processed and retry_count <= MAX_RETRIES:
            try:
                with tab_lock:  
                    sb.switch_to_tab(tab_id)
                    success = safe_open(sb, url, timeout=10)
                    if not success:
                        print(f"[Worker {worker_id}] Timeout loading {url}")
                        retry_count += 1
                        continue
                    sb.sleep(3)
                    title = sb.get_title()
                    cf_retry = 0
                    while title == "Just a moment..." and cf_retry < 6:
                        print(f"[Worker {worker_id}] Cloudflare challenge on {url}, waiting 10s")
                        ok = safe_open(sb, url, timeout=20)
                        if not ok:
                            break
                        sb.sleep(10)
                        title = sb.get_title()
                        cf_retry += 1
                    if title == "Just a moment...":
                        print(f"[Worker {worker_id}] Still blocked: {url}")
                        retry_count += 1
                        continue
                    html = sb.get_page_source()
                soup = BeautifulSoup(html, "html.parser")
                info = extract_company_info(soup)
                result_queue.put((url, clean_company(info)))
                url_processed = True
                print(f"[Worker {worker_id}] and url: {url}")
            except Exception as e:
                print(f"[Worker {worker_id}] Failed: {url} - {e}")
                url_processed = True
        if not url_processed:
            print(f"[Worker {worker_id}]  Giving up on {url}")


# --- Setup ---
print("Launching main browser and solving captcha...")
sb = sb_cdp.Chrome(guest=True)
sb.open("https://www.manta.com/")
sb.sleep(20)
sb.solve_captcha()
sb.wait_for_element_absent("input[disabled]")
sb.sleep(10)
print(" Verified")

NUM_WORKERS = 5
all_urls = list(companies_dict.keys())[3000:4000]
chunk_size = len(all_urls) // NUM_WORKERS + 1
url_chunks = [all_urls[i:i + chunk_size] for i in range(0, len(all_urls), chunk_size)]

# Open tabs and record their IDs
tab_ids = [sb.get_active_tab()]  # first tab = the original one
for i in range(NUM_WORKERS - 1):
    sb.open_new_tab()
    tab_ids.append(sb.get_active_tab())
    print(f"Opened tab {i + 2}: {tab_ids[-1]}")

print("Tabs:", sb.get_tabs())

threads = []
start_time = time.time()

for i, chunk in enumerate(url_chunks):
    t = threading.Thread(target=worker_batch, args=(sb, tab_ids[i], chunk, result_queue, i + 1), daemon=True)
    threads.append(t)
    t.start()
    print(f"Started worker {i + 1}")

try:
    while any(t.is_alive() for t in threads):
        time.sleep(2)
except KeyboardInterrupt:
    print("\nInterrupted by user")

elapsed = time.time() - start_time
print(f"\nTotal time: {elapsed:.1f} seconds")

sb.driver.quit()
