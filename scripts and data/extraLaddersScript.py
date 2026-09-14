import json
import time
import requests
from bs4 import BeautifulSoup

FRIENDS_HANDLES = [] 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_cf_problem_map():
    url = "https://codeforces.com/api/problemset.problems"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        data = res.json()
        if data['status'] == 'OK':
            problem_map = {}
            for p in data['result']['problems']:
                if 'contestId' in p and 'index' in p:
                    problem_map[p['name']] = {'contestId': p['contestId'], 'index': p['index']}
            return problem_map
    except: pass
    return {}

def scrape_problem_html(session, contestId, index):
    url = f"https://codeforces.com/contest/{contestId}/problem/{index}"
    for _ in range(3):
        try:
            res = session.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                statement = soup.find('div', class_='problem-statement')
                if statement:
                    for img in statement.find_all('img'):
                        if img.get('src') and img['src'].startswith('/'):
                            img['src'] = "https://codeforces.com" + img['src']
                    return str(statement)
            elif res.status_code == 403: time.sleep(3)
            else: break
        except: time.sleep(3)
    return None

def fetch_friend_code(session, handle, contest_id, sub_id):
    url = f"https://codeforces.com/contest/{contest_id}/submission/{sub_id}"
    try:
        time.sleep(1.5)
        res = session.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        code_block = soup.find('pre', id='program-source-text')
        if code_block: return code_block.text
    except: pass
    return None

def main():
    print("🚀 Starting Incremental Updater...")
    
    try:
        with open("extra_ladders.json", "r", encoding="utf-8") as f:
            extra_ladders = json.load(f)
    except FileNotFoundError:
        print("Error: 'extra_ladders.json' not found.")
        return

    cf_map = fetch_cf_problem_map()
    if not cf_map: return

    target_problems = {}
    for rating_problems in extra_ladders.values():
        for p in rating_problems:
            name = p.get('name')
            if name in cf_map:
                target_problems[f"{cf_map[name]['contestId']}_{cf_map[name]['index']}"] = name

    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Append new HTML data to problems_data.js
    with open("problems_data.js", "a", encoding="utf-8") as f_out:
        for rating_str, problems in extra_ladders.items():
            print(f"\n⚡ Fetching HTML for Rating {rating_str}...")
            scraped_problems = []
            for i, p in enumerate(problems[:100]):
                name = p['name']
                print(f"   -> Fetching {i+1}/{len(problems[:100])}: {name}", end="\r")
                if name in cf_map:
                    cid = cf_map[name]['contestId']
                    idx = cf_map[name]['index']
                    time.sleep(1)
                    html = scrape_problem_html(session, cid, idx)
                    if html:
                        scraped_problems.append({
                            "contestId": cid, "index": idx, "name": name, 
                            "solvedCount": p['solvedCount'], "html": html
                        })
            
            if scraped_problems:
                json_str = json.dumps(scraped_problems).replace("</", "<\\/")
                f_out.write(f'\nALL_PROBLEMS["{rating_str}"] = {json_str};\n')
                print(f"\n✅ Added Rating {rating_str} to problems_data.js")

    # 2. Append new friends codes to friends_codes.js
    compiled_codes = {}
    for handle in FRIENDS_HANDLES:
        print(f"\nFetching friends codes for {handle}...")
        url = f"https://codeforces.com/api/user.status?handle={handle}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
        except: continue
        
        if data.get("status") != "OK": continue

        for sub in data.get("result", []):
            if sub.get("verdict") == "OK" and "problem" in sub:
                c_id = sub["problem"].get("contestId")
                idx = sub["problem"].get("index")
                if not c_id or not idx: continue
                
                pid = f"{c_id}_{idx}"
                if pid in target_problems:
                    prob_name = target_problems[pid]
                    if prob_name not in compiled_codes:
                        compiled_codes[prob_name] = {}
                    
                    if handle not in compiled_codes[prob_name]:
                        print(f"   -> Downloading code for {prob_name}...")
                        code_text = fetch_friend_code(session, handle, c_id, sub["id"])
                        if code_text:
                            compiled_codes[prob_name][handle] = code_text

    if compiled_codes:
        with open("friends_codes.js", "a", encoding="utf-8") as f_out:
            json_str = json.dumps(compiled_codes).replace("</", "<\\/")
            # Object.assign dynamically adds the new codes to the existing FRIENDS_CODES object
            f_out.write(f'\nObject.assign(FRIENDS_CODES, {json_str});\n')
            print("\n✅ Appended new codes to friends_codes.js")

    print("\n🎉 All Done! Just refresh your HTML file and the new ratings will appear.")

if __name__ == "__main__":
    main()