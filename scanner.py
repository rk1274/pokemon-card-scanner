import cv2
import easyocr
import re
import sqlite3

READER = easyocr.Reader(['en'], gpu=False)

def extract_card_details(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    h, w, _ = img.shape
    
    resized_top = crop_and_resize(img, w, 0, int(h * 0.12), 0.65)
    resized_bottom = crop_and_resize(img, w, int(h * 0.85), h, 1.0)
            
    return extract_name(resized_top), extract_number(resized_bottom)

def crop_and_resize(img, width, l, r, horizontal_crop):
    crop = img[l:r, 0:int(width * horizontal_crop)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

def extract_name(top_img):
    results = READER.readtext(top_img)

    card_name = None
    if results:
        results.sort(key=lambda x: x[0][0][0])
        
        for (bbox, text, prob) in results:
            cleaned_text = text.strip()
            if len(cleaned_text) < 3:
                continue
                
            cleaned_text = cleaned_text.replace("€X", " ex").replace("EX", " ex")
            cleaned_text = "".join(c for c in cleaned_text if c.isalnum() or c in " -").strip()
            
            if check_name_in_db(cleaned_text):
                card_name = cleaned_text
                print(f"Database validated name match found: '{card_name}'")
                break
                
        if not card_name:
            for (bbox, text, prob) in results:
                cleaned_text = "".join(c for c in text if c.isalnum() or c in " -").strip()
                if len(cleaned_text) >= 3:
                    card_name = cleaned_text
                    break

    return card_name

def extract_number(bottom_img):
    results = READER.readtext(bottom_img)
        
    card_number = None
    card_number_pattern = re.compile(r'(\d+)\s*/\s*(\d+)')
    
    for (bbox, text, prob) in results:
        clean_text = text.replace('O', '0').replace('I', '1')
        match = card_number_pattern.search(clean_text)
        if match:
            card_number = match.group(1)
            break

    return card_number

def check_name_in_db(name_to_check):
    """Returns True if the name exists anywhere in our local Pokémon card table."""
    conn = sqlite3.connect("pokemon_cards.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM cards WHERE LOWER(name) = LOWER(?) LIMIT 1", (name_to_check,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None