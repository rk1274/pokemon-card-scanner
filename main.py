import scanner
import fetch_cards
import matcher

def get_card_info(image_path):
    name, num = scanner.extract_card_details(image_path)
    print(f"OCR Detected: Name='{name}', Number='{num}'")

    results = fetch_cards.search_pokemon_cards_hybrid(name, num)

    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        match = matcher.find_best_match(image_path, num, results)
        return match
    else:
        return None

if __name__ == "__main__":
    match = get_card_info("test_cards/shiny_shinx.png")
    if match:
        print("Found!\n",match,"\n")
    else:
        print("No match found.\n")

    match = get_card_info("test_cards/cinccino_fa_2.png")
    if match:
        print("Found!\n",match,"\n")
    else:
        print("No match found.\n")

    match = get_card_info("test_cards/1.jpg")
    if match:
        print("Found!\n",match,"\n")
    else:
        print("No match found.\n")
