import json
import time
import requests
from bs4 import BeautifulSoup

# Configuration headers for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_cf_problem_map():
    # Fetch all problems from CF API to map names to contestId and index
    print("Fetching official problem list from Codeforces API...")
    url = "https://codeforces.com/api/problemset.problems"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        if data['status'] == 'OK':
            problem_map = {}
            for p in data['result']['problems']:
                if 'contestId' in p and 'index' in p:
                    # Use problem name as the dictionary key
                    problem_map[p['name']] = {
                        'contestId': p['contestId'],
                        'index': p['index']
                    }
            print(f"Successfully loaded {len(problem_map)} problems from Codeforces.")
            return problem_map
    except Exception as e:
        print(f"Error fetching CF API: {e}")
    return {}

def scrape_problem_html(session, contestId, index):
    # Fetch problem statement HTML directly from Codeforces
    url = f"https://codeforces.com/contest/{contestId}/problem/{index}"
    
    for attempt in range(3):
        try:
            res = session.get(url, headers=HEADERS, timeout=15)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                statement = soup.find('div', class_='problem-statement')
                
                if statement:
                    # Fix image links for offline rendering
                    for img in statement.find_all('img'):
                        if img.get('src') and img['src'].startswith('/'):
                            img['src'] = "https://codeforces.com" + img['src']
                    return str(statement)
            elif res.status_code == 403:
                time.sleep(3)
            else:
                break
        except Exception as e:
            time.sleep(3)
    return None

def main():
    print("Starting Ultimate Data Fetcher for CF Platform...")
    
    input_file = "all_ladders.json"
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            all_ladders = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found.")
        return

    # Build the smart name map
    cf_map = fetch_cf_problem_map()
    if not cf_map:
        print("Failed to map problems. Exiting.")
        return

    output_lines = ["const ALL_PROBLEMS = {};\n\n"]
    session = requests.Session()
    
    for rating_str in sorted(all_ladders.keys(), key=lambda x: int(x)):
        problems = all_ladders[rating_str][:100]
        print(f"\nProcessing Rating {rating_str}...")
        
        scraped_problems = []
        
        for i, prob in enumerate(problems):
            name = prob['name']
            print(f"   -> Fetching {i+1}/{len(problems)} ({name})...", end="\r")
            
            # Smart matching: Find contestId and index using the problem name
            if name in cf_map:
                contest_id = cf_map[name]['contestId']
                index = cf_map[name]['index']
                
                time.sleep(1)
                html_content = scrape_problem_html(session, contest_id, index)
                
                if html_content:
                    scraped_problems.append({
                        "contestId": contest_id,
                        "index": index,
                        "name": name,
                        "solvedCount": prob['solvedCount'], # The C2 Ladders Frequency
                        "html": html_content
                    })
            else:
                print(f"\n   [!] Could not find '{name}' in CF API.")
        
        print(f"\nSuccessfully fetched {len(scraped_problems)}/{len(problems)} problems.")
        
        if scraped_problems:
            # Escape closing script tags to prevent JS syntax errors in HTML
            json_str = json.dumps(scraped_problems).replace("</", "<\\/")
            output_lines.append(f'ALL_PROBLEMS["{rating_str}"] = {json_str};\n')

    output_file = "problems_data.js"
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
        
    print(f"\nData successfully generated in '{output_file}'!")

if __name__ == "__main__":
    main()
