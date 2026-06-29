import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

import scanner
import fetch_cards
import matcher

app = Flask(__name__)

# Temporary workspace to hold the user's uploaded photo during analysis
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_web_scan(image_path):
    """Executes your exact matching logic pipeline"""
    name, num = scanner.extract_card_details(image_path)
    print(f"[Web Logger] OCR Extracted -> Name: '{name}', Number: '{num}'")

    results = fetch_cards.search_pokemon_cards_hybrid(name, num)

    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        match = matcher.find_best_match(image_path, num, results)
        return match
    else:
        return None

@app.route('/', methods=['GET'])
def home_dashboard():
    """Serves your frontend web UI dashboard"""
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_endpoint():
    """Receives image streams asynchronously from the web interface"""
    if 'card_image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file uploaded'}), 400
        
    file = request.files['card_image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Process the image with your matching pipeline
            matched_card_data = process_web_scan(file_path)
            
            # Wipe the temporary image file out of memory to keep the server clean
            os.remove(file_path)
            
            if matched_card_data:
                return jsonify({'success': True, 'card': matched_card_data})
            else:
                return jsonify({'success': False, 'message': 'Card details verified but no database match discovered.'})
                
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'success': False, 'message': f'Server pipeline error: {str(e)}'}), 500

if __name__ == '__main__':
    # Runs locally for development testing
    app.run(debug=True, port=5000)