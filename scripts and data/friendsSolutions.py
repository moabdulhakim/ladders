import os
import json
import time
import random
import requests
from playwright.sync_api import sync_playwright, TimeoutError

FRIENDS_HANDLES = [
    "jiangly", "tourist", "Errichto", "neal", "ecnerwala", 
    "Benq", "Radewoosh", "Um_nik", "galen_colin", "tmwilliamlin168", "Gamal74"
]

# We use standard requests for the API because CF rarely blocks API calls
def fetch_cf_problem_map():
    print("Fetching official problem list from Codeforces API...")
    url = "https://codeforces.com/api/problemset.problems"
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        if data['status'] == 'OK':
            problem_map = {}
            for p in data['result']['problems']:
                if 'contestId' in p and 'index' in p:
                    problem_map[p['name']] = {
                        'contestId': p['contestId'],
                        'index': p['index']
                    }
            return problem_map
    except Exception as e:
        print(f"Error fetching CF API: {e}")
    return {}

def save_progress(compiled_codes, output_file):
    # Save incrementally to avoid data loss
    json_str = json.dumps(compiled_codes).replace("</", "<\\/")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"const FRIENDS_CODES = {json_str};\n")

def main():
    print("🚀 Starting Playwright Browser Aggregator (100% Anti-Cloudflare)...")
    
    output_file = "friends_codes.js"
    compiled_codes = {}

    # --- AUTO-RESUME LOGIC ---
    if os.path.exists(output_file):
        print(f"📂 Found existing '{output_file}'. Loading progress...")
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("const FRIENDS_CODES = "):
                    content = content[len("const FRIENDS_CODES = "):]
                if content.endswith(";"):
                    content = content[:-1]
                compiled_codes = json.loads(content.replace("<\\/", "</"))
            print(f"✅ Loaded {len(compiled_codes)} problems. Skipping existing downloads.")
        except Exception as e:
            print(f"⚠️ Could not parse existing file: {e}")

    try:
        with open("all_ladders.json", "r", encoding="utf-8") as f:
            ladders = json.load(f)
    except FileNotFoundError:
        print("❌ Error: 'all_ladders.json' not found.")
        return

    cf_map = fetch_cf_problem_map()
    if not cf_map:
        return

    target_problems = {}
    for rating_problems in ladders.values():
        for p in rating_problems:
            name = p.get('name')
            if name in cf_map:
                target_problems[f"{cf_map[name]['contestId']}_{cf_map[name]['index']}"] = name

    download_tasks = []
    
    print("\n⚡ Indexing submissions via API...")
    for handle in FRIENDS_HANDLES:
        url = f"https://codeforces.com/api/user.status?handle={handle}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
        except:
            continue

        if data.get("status") != "OK":
            continue

        handle_prob_count = {}
        
        for sub in data.get("result", []):
            if sub.get("verdict") == "OK" and "problem" in sub:
                c_id = sub["problem"].get("contestId")
                idx = sub["problem"].get("index")
                if not c_id or not idx: continue
                
                pid = f"{c_id}_{idx}"
                if pid in target_problems:
                    prob_name = target_problems[pid]
                    
                    # Skip if already downloaded
                    if prob_name in compiled_codes and handle in compiled_codes[prob_name]:
                        continue
                    
                    key = f"{handle}_{prob_name}"
                    if handle_prob_count.get(key, 0) >= 2:
                        continue
                        
                    handle_prob_count[key] = handle_prob_count.get(key, 0) + 1
                    download_tasks.append((handle, prob_name, c_id, sub["id"]))

    total_tasks = len(download_tasks)
    if total_tasks == 0:
        print("\n✨ All codes are already downloaded! Nothing to do.")
        return
        
    print(f"\n📦 Found {total_tasks} NEW submissions to download.")
    
    # --- ENTER PLAYWRIGHT (REAL BROWSER) ---
    with sync_playwright() as p:
        # headless=False opens a visible browser so Cloudflare trusts it completely
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        print("\n🌐 Opening Codeforces...")
        page.goto("https://codeforces.com/")
        
        input("🛑 ACTION REQUIRED: Please log in to Codeforces in the opened browser window. Once logged in, press ENTER here to continue...")
        
        successful_downloads = 0

        for i, task in enumerate(download_tasks, 1):
            handle, prob_name, c_id, sub_id = task
            url = f"https://codeforces.com/contest/{c_id}/submission/{sub_id}"
            
            try:
                # Small delay to mimic human reading speed
                time.sleep(random.uniform(1.5, 3.0))
                
                page.goto(url)
                
                # Wait for the code block to appear (handles slow connections and CF checks)
                page.wait_for_selector("pre#program-source-text", timeout=15000)
                code_text = page.locator("pre#program-source-text").inner_text()
                status = "Success"
                
            except TimeoutError:
                status = "Timeout/Blocked"
                code_text = None
            except Exception as e:
                status = f"Error: {str(e)}"
                code_text = None
            
            print(f"[{i}/{total_tasks}] {prob_name} by {handle} -> {status}")
            
            if code_text:
                successful_downloads += 1
                if prob_name not in compiled_codes:
                    compiled_codes[prob_name] = {}
                
                if handle in compiled_codes[prob_name]:
                    separator = "\n\n/* =========================================================\n   OLDER SUBMISSION (Alternative Approach)\n========================================================= */\n\n"
                    if "OLDER SUBMISSION" not in compiled_codes[prob_name][handle]:
                        compiled_codes[prob_name][handle] += separator + code_text
                else:
                    compiled_codes[prob_name][handle] = code_text
                
                save_progress(compiled_codes, output_file)

        print(f"\n\n🎉 Done! Downloaded {successful_downloads}/{total_tasks} new codes.")
        browser.close()

if __name__ == "__main__":
    main()



# ---------------

""" Better in JS (IMPORTANT NOTE: THIS SCRIPT MAY BAN YOUR ACCOUNT, AVOID USING IT FOR YOUR MAIN ACCOUNT, IT JUST FOR USE IN AN ALTERNATIVE ACCOUNT)

// 1. Replace this variable with the exact content of your all_ladders.json file
const LADDERS_DATA = ;

let compiledCodes = {};
const FRIENDS = ["jiangly"];

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function downloadJSFile(data, filename) {
    let jsonStr = JSON.stringify(data).replace(/<\//g, "<\\/");
    let finalOutput = `const FRIENDS_CODES = ${jsonStr};\n`;
    let blob = new Blob([finalOutput], {type: "application/javascript"});
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}

// 🛡️ Safe Fetcher with Automatic Exponential Backoff for API Rate Limits
async function safeApiFetch(url) {
    let backoff = 2000; // Start with 2 seconds wait on fail
    while (true) {
        try {
            let res = await fetch(url);
            
            // Handle HTTP 429 Too Many Requests
            if (res.status === 429) {
                console.warn(`⚠️ HTTP 429 Rate Limit. Pausing for ${backoff/1000}s...`);
                await sleep(backoff);
                backoff += 2000;
                continue;
            }
            
            let data = await res.json();
            
            // Handle CF API specific limit error
            if (data.status === "FAILED" && data.comment && data.comment.toLowerCase().includes("limit")) {
                console.warn(`⚠️ API Rate Limit Hit ("${data.comment}"). Pausing for ${backoff/1000}s...`);
                await sleep(backoff);
                backoff += 2000;
                continue;
            }
            
            return data; // Success
        } catch (e) {
            console.warn(`⚠️ Network issue fetching API. Retrying in 5s...`);
            await sleep(5000);
        }
    }
}

async function startMasterScraper() {
    console.log("🚀 Starting Rate-Limit-Proof Master Scraper...");
    
    // Step 1: Fetch API mapping securely
    console.log("Fetching official CF problems list...");
    let data = await safeApiFetch("https://codeforces.com/api/problemset.problems");
    let problemMap = {};
    data.result.problems.forEach(p => {
        if(p.contestId && p.index) problemMap[p.name] = `${p.contestId}_${p.index}`;
    });

    let targetProblems = {};
    for (let rating in LADDERS_DATA) {
        LADDERS_DATA[rating].forEach(p => {
            if (problemMap[p.name]) {
                targetProblems[problemMap[p.name]] = p.name;
            }
        });
    }

    // Step 2: Build tasks list from API (Using Safe Fetch)
    let downloadTasks = [];
    for (let handle of FRIENDS) {
        console.log(`⚡ Indexing API for ${handle}...`);
        
        let d = await safeApiFetch(`https://codeforces.com/api/user.status?handle=${handle}`);
        let handleProbCount = {};
        
        if (d && d.status === "OK") {
            for (let sub of d.result) {
                if (sub.verdict === "OK" && sub.problem) {
                    let pid = `${sub.problem.contestId}_${sub.problem.index}`;
                    if (targetProblems[pid]) {
                        let probName = targetProblems[pid];
                        let key = `${handle}_${probName}`;
                        handleProbCount[key] = (handleProbCount[key] || 0) + 1;
                        
                        if (handleProbCount[key] <= 2) {
                            downloadTasks.push({ 
                                handle, 
                                probName, 
                                url: `https://codeforces.com/contest/${sub.problem.contestId}/submission/${sub.id}` 
                            });
                        }
                    }
                }
            }
        }
        await sleep(1500); // Standard safe delay between user indexing
    }

    console.log(`📦 Found ${downloadTasks.length} codes to download.`);
    console.log("⚠️ PLEASE ALLOW POPUPS IF YOUR BROWSER ASKS!");

    // Step 3: Open the Worker Tab
    let workerTab = window.open("about:blank", "WorkerTab");
    if (!workerTab) {
        console.error("❌ Popup blocked! Please allow popups for Codeforces and run the script again.");
        return;
    }

    let successCount = 0;

    // Step 4: Navigate and Extract with HTML Rate-Limit Detection
    for (let i = 0; i < downloadTasks.length; i++) {
        let task = downloadTasks[i];
        console.log(`[${i+1}/${downloadTasks.length}] Navigating to ${task.probName} by ${task.handle}...`);
        
        workerTab.location.href = task.url;

        let codeFound = false;
        let attempts = 0;
        
        while (!codeFound && attempts < 20) {
            await sleep(1000); 
            try {
                let codeBlock = workerTab.document.querySelector("pre#program-source-text");
                let bodyText = workerTab.document.body ? workerTab.document.body.innerText.toLowerCase() : "";

                // 🛡️ Detect "Rate limit exceeded" text on the actual worker page
                if (bodyText.includes("limit exceeded") || bodyText.includes("too many requests")) {
                    console.warn(`🛑 Page Rate Limit Detected! Sleeping for 20s before reloading...`);
                    await sleep(20000);
                    workerTab.location.reload(); // Refresh the page automatically
                    attempts = 0; // Reset attempts after reload
                    continue;
                }

                if (codeBlock) {
                    let codeText = codeBlock.innerText;
                    if (!compiledCodes[task.probName]) compiledCodes[task.probName] = {};
                    
                    if (compiledCodes[task.probName][task.handle]) {
                         let separator = "\n\n/* =========================================================\n   OLDER SUBMISSION \n========================================================= */\n\n";
                         if(!compiledCodes[task.probName][task.handle].includes("OLDER SUBMISSION")) {
                             compiledCodes[task.probName][task.handle] += separator + codeText;
                         }
                    } else {
                        compiledCodes[task.probName][task.handle] = codeText;
                    }
                    
                    codeFound = true;
                    successCount++;
                    console.log(`   ✅ Success!`);
                }
            } catch (err) {
                // Ignore cross-origin DOM errors during page load
            }
            attempts++;
        }

        if (!codeFound) {
            console.log(`   ⚠️ Failed or Code hidden for ${task.handle} after multiple attempts.`);
        }

        if (successCount > 0 && successCount % 500 === 0) {
            console.log(`💾 Reached ${successCount} downloads! Auto-saving backup...`);
            downloadJSFile(compiledCodes, `friends_codes_backup_${successCount}.js`);
        }

        // Base 3 seconds delay + Random 1-3 seconds to prevent triggering page limits
        await sleep(30000 + Math.random() * 15000);
    }

    workerTab.close();
    console.log(`🎉 ALL DONE! Downloaded ${successCount} codes successfully.`);
    downloadJSFile(compiledCodes, "friends_codes.js");
}

startMasterScraper();
"""