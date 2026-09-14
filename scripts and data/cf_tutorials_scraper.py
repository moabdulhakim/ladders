import json
try:
    from datasets import load_dataset
except ImportError:
    print("Please install the datasets library first: pip install datasets")
    exit(1)

def main():
    print("🚀 Starting the All-in-One Tutorials Scraper...")
    
    # 1. Read your ladders (if available)
    target_problems = set()
    original_names = {}
    try:
        with open("all_ladders.json", "r", encoding="utf-8") as f:
            ladders = json.load(f)
            for rating, problems in ladders.items():
                for p in problems:
                    if 'name' in p:
                        name_lower = p['name'].strip().lower()
                        target_problems.add(name_lower)
                        original_names[name_lower] = p['name'].strip()
        print(f"✅ Loaded {len(target_problems)} target problems from 'all_ladders.json'.")
    except FileNotFoundError:
        print("⚠️ 'all_ladders.json' not found. Make sure it's in the same folder.")

    # 2. Download/Load dataset from Hugging Face (Downloads ONLY ONCE)
    print("⏳ Downloading/Loading dataset from Hugging Face...")
    try:
        dataset = load_dataset("open-r1/codeforces", split="train")
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return
        
    all_tutorials = {}
    filtered_tutorials = {}
    
    print("🔍 Processing all 10,000+ tutorials...")
    
    # 3. Process the dataset
    for row in dataset:
        p_name = str(row.get('title', '')).strip()
        p_name_lower = p_name.lower()
        editorial_text = row.get('editorial')
        
        # Ensure the problem has a valid editorial
        if p_name and editorial_text and str(editorial_text).strip() and str(editorial_text).strip() != "None":
            
            # Save to the "All" collection (Your offline backup)
            all_tutorials[p_name] = str(editorial_text)
            
            # Check if it's in your ladders
            if p_name_lower in target_problems:
                orig_name = original_names.get(p_name_lower, p_name)
                filtered_tutorials[orig_name] = str(editorial_text)

    # 4. Save the full archive (The big JSON backup)
    with open("all_cf_tutorials.json", "w", encoding="utf-8") as f:
        json.dump(all_tutorials, f, ensure_ascii=False, indent=4)
    print(f"📦 Saved ALL {len(all_tutorials)} tutorials safely to 'all_cf_tutorials.json'")

    # 5. Save the filtered JS file (The lightweight file for your website)
    if target_problems:
        json_str = json.dumps(filtered_tutorials).replace("</", "<\/")
        with open("my_tutorials.js", "w", encoding="utf-8") as f:
            f.write(f"const PROBLEM_TUTORIALS = {json_str};\n")
        print(f"🚀 Saved {len(filtered_tutorials)} filtered tutorials to 'my_tutorials.js'")
        print("✨ You are ready to go offline!")

if __name__ == "__main__":
    main()
