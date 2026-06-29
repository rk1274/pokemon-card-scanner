import os
import requests
import sqlite3

# Base configuration
BASE_URL = "https://api.pokemontcg.io/v2/cards"
# Tip: Sign up at dev.pokemontcg.io for a free key if you hit rate limits
API_KEY = "a7757796-071a-4bcb-a12c-ea189f70c440" 

def search_pokemon_cards(name,num):
    """Searches the Pokémon TCG API using their custom query syntax."""
    headers = {}
    if API_KEY:
        headers["X-Api-Key"] = API_KEY
        
    params = {
        "q":"name:"+name+" number:"+str(num),
        "select": "id,name,set,number,types,images"
    }
    
    response = requests.get(BASE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []
    
def search_pokemon_cards_hybrid(card_name, card_number):
    conn = sqlite3.connect("pokemon_cards.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    base_name = card_name.split()[0] if card_name else ""
    clean_num = str(card_number).lstrip("0")
    
    # 1. Try the exact match first
    query = """
        SELECT * FROM cards 
        WHERE (number = ? OR number = ?) 
        AND name LIKE ?
    """
    cursor.execute(query, (clean_num, f"0{clean_num}", f"%{base_name}%"))
    rows = cursor.fetchall()
    
    # 2. SMART FALLBACK: If 0 cards found, the OCR likely cut off a digit (e.g., read 19 instead of 119)
    if len(rows) == 0 and clean_num:
        print(f"No exact match for '{clean_num}'. Trying wildcard suffix matching...")
        fallback_query = """
            SELECT * FROM cards 
            WHERE name LIKE ? 
            AND (number LIKE ? OR number = ?)
        """
        # This matches any number ending in your clean_num (like %19 will match 119, 019, 219)
        cursor.execute(fallback_query, (f"%{base_name}%", f"%{clean_num}", clean_num))
        rows = cursor.fetchall()

    conn.close()
    
    candidates = []
    for row in rows:
        candidates.append({
            "id": row["id"],
            "name": row["name"],
            "set": {"name": row["set_name"]},
            "number": row["number"],
            "types": row["types"].split(", "),
            "image_url": row["image_url"]
        })
    return candidates