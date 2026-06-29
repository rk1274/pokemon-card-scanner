import cv2
import numpy as np
import requests

def find_best_match(user_image_path, card_number, candidates):
    """
    Takes a user's photo and the OCR'd card number, 
    fetches candidates from the API, and finds the exact match using ORB.
    """
    orb = cv2.ORB_create(nfeatures=1500)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    user_img = cv2.imread(user_image_path, cv2.IMREAD_GRAYSCALE)
    if user_img is None:
        return "User image not found."
    
    kp_user, des_user = orb.detectAndCompute(user_img, None)
    if des_user is None:
        return "Could not find any distinct features in your photo."
    
    best_candidate = None
    max_good_matches = 0

    for card in candidates:
        image_url = card["image_url"]
        
        try:
            resp = requests.get(image_url, timeout=5)
            img_array = np.asarray(bytearray(resp.content), dtype=np.uint8)
            cand_img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        except Exception as e:
            print(f"Skipping {card['name']} due to download error.")
            continue

        kp_cand, des_cand = orb.detectAndCompute(cand_img, None)
        if des_cand is None:
            continue
            
        matches = bf.match(des_user, des_cand)
        
        good_matches = [m for m in matches if m.distance < 40]
        # print(f"-> {card['name']} ({card['set']['name']}): {len(good_matches)} match points.")
        
        if len(good_matches) > max_good_matches:
            max_good_matches = len(good_matches)
            best_candidate = card

    if max_good_matches > 15:
        return {
            "name": best_candidate["name"],
            "set": best_candidate["set"]["name"],
            "number": best_candidate["number"],
            "types": best_candidate.get("types", ["Unknown"]),
            "confidence_points": max_good_matches
        }
    else:
        return "Could not reliably match the card artwork to the candidates."
