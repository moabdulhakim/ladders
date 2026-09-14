import json
import csv
import ast
import re

def main():
    print("Starting offline codes extractor...")

    # 1. Load target problems from all_ladders.json
    target_problems = set()
    original_names = {}
    
    try:
        with open("all_ladders.json", "r", encoding="utf-8") as f:
            ladders = json.load(f)
            for rating, problems in ladders.items():
                for p in problems:
                    if 'name' in p:
                        # Normalize name: lowercase and remove extra spaces
                        name = p['name'].strip()
                        name_lower = name.lower()
                        target_problems.add(name_lower)
                        original_names[name_lower] = name
                        
                        # Also add a version without the prefix (e.g., "A. ") just in case
                        no_prefix = re.sub(r'^[A-Z][0-9]*\.\s*', '', name).lower()
                        target_problems.add(no_prefix)
                        original_names[no_prefix] = name
                        
        print(f"Loaded {len(target_problems)} problem variations from ladders.")
    except FileNotFoundError:
        print("Error: all_ladders.json not found.")
        return

    # 2. Parse the CSV file and extract matching solutions
    friends_codes = {}
    matched_count = 0
    csv_file = "raw_dataset_codes.csv"
    
    # The virtual friend name that will appear in your UI
    VIRTUAL_FRIEND_NAME = "Optimal_Solution"

    print(f"Reading {csv_file}...")
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            # Use csv.DictReader to automatically handle columns by name
            reader = csv.DictReader(f)
            
            for row in reader:
                # Get the problem name from the CSV
                csv_name = row.get("problem_name", "").strip()
                if not csv_name:
                    continue
                
                # Normalize the CSV problem name
                csv_name_lower = csv_name.lower()
                csv_name_no_prefix = re.sub(r'^[a-z][0-9]*\.\s*', '', csv_name_lower)
                
                # Check if this problem exists in our ladders
                matched_orig_name = None
                if csv_name_lower in target_problems:
                    matched_orig_name = original_names[csv_name_lower]
                elif csv_name_no_prefix in target_problems:
                    matched_orig_name = original_names[csv_name_no_prefix]
                
                if matched_orig_name:
                    raw_code = row.get("problem_solution", "").strip()
                    clean_code = ""
                    
                    # Clean the code string: Convert stringified list "['...']" to actual string
                    if raw_code.startswith("[") and raw_code.endswith("]"):
                        try:
                            # Safely evaluate the string literal
                            parsed_list = ast.literal_eval(raw_code)
                            if isinstance(parsed_list, list) and len(parsed_list) > 0:
                                clean_code = parsed_list[0]
                                
                                # Fix escaped newlines and tabs if any remain
                                clean_code = clean_code.replace('\\n', '\n').replace('\\t', '\t')
                        except:
                            # Fallback if evaluation fails
                            clean_code = raw_code
                    else:
                        clean_code = raw_code

                    if clean_code:
                        if matched_orig_name not in friends_codes:
                            friends_codes[matched_orig_name] = {}
                        
                        friends_codes[matched_orig_name][VIRTUAL_FRIEND_NAME] = clean_code
                        matched_count += 1
                        
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Please ensure the file name is correct.")
        return

    print(f"Successfully extracted C++ solutions for {matched_count} problems.")

    # 3. Export to friends_codes.js format for the website
    output_file = "friends_codes.js"
    json_str = json.dumps(friends_codes, indent=4).replace("</", "<\\/")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"const FRIENDS_CODES = {json_str};\n")

    print(f"Saved successfully to {output_file}. Your UI will now read this automatically!")

if __name__ == "__main__":
    main()
