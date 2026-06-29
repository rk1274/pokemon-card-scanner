import sqlite3
import os
import json

DB_NAME = "pokemon_cards.db"
JSON_DIR = os.path.join("cards_data", "cards", "en")
# Path to the sets mapping file you just found
SETS_FILE = os.path.join("cards_data", "sets", "en.json")

def init_database():
    if not os.path.exists(JSON_DIR):
        print(f"Error: Could not find JSON directory at {JSON_DIR}.")
        return

    # 1. Load the set mappings first so we can translate IDs to human-readable Names
    set_name_mapping = {}
    if os.path.exists(SETS_FILE):
        print("Loading set name translations...")
        with open(SETS_FILE, "r", encoding="utf-8") as sf:
            sets_list = json.load(sf)
            for s in sets_list:
                set_name_mapping[s["id"]] = s["name"]
    else:
        print(f"Warning: {SETS_FILE} not found. Set names will default to file IDs.")

    # 2. Connect to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            name TEXT,
            set_name TEXT,
            number TEXT,
            types TEXT,
            image_url TEXT
        )
    ''')
    
    print("Reading local JSON files...")
    insert_query = '''
        INSERT OR REPLACE INTO cards (id, name, set_name, number, types, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    
    total_inserted = 0

    # 3. Loop through every single set JSON file
    for filename in os.listdir(JSON_DIR):
        if filename.endswith(".json"):
            # The file name itself (minus '.json') is the Set ID! (e.g., "base1")
            set_id = filename.replace(".json", "")
            
            # Look up the human-readable set name from our mapping dictionary
            set_name = set_name_mapping.get(set_id, set_id.upper())
            
            file_path = os.path.join(JSON_DIR, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    cards_list = json.load(f)
                    
                    for card in cards_list:
                        types_str = ", ".join(card.get("types", ["Unknown"]))
                        
                        cursor.execute(insert_query, (
                            card["id"],
                            card["name"],
                            set_name, # Storing the cleanly mapped string!
                            card["number"],
                            types_str,
                            card.get("images", {}).get("small", "")
                        ))
                        total_inserted += 1
                except Exception as e:
                    print(f"Skipping error file {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully populated SQL Database! Total cards registered: {total_inserted}")

if __name__ == "__main__":
    init_database()