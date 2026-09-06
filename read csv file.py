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