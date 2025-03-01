from flask import Flask, request, jsonify, render_template
import os
from PIL import Image
import io
import google.generativeai as genai
from huggingface_hub import InferenceClient
import time

app = Flask(__name__)

# Google Generative AI configuration for text generation
def generate_output(model_name, user_input):
    api_key = "AIzaSyDBH2_fjAeB64R-4uWbwzlCPXb9r8lXujA"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)

    try:
        t = {"parts": [{"text": user_input}]}
        response = model.generate_content(t)
        generated_text = response.text.strip()
        return generated_text
    except Exception as e:
        return f"An error occurred: {e}"

# Hugging Face configuration for image generation
def generate_image(prompt, model="jbilcke-hf/flux-dev-panorama-lora-2", retries=5, delay=10):
    client = InferenceClient(model, token="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")

    for attempt in range(retries):
        try:
            return client.text_to_image(prompt)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    raise Exception("All retries failed. Please try again later.")

# Model name for text generation
MODEL_NAME = "tunedModels/outfitsuggestiongenerator-usqw4b296kfe"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_outfit():
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # Extract fields
        style_idea = data.get("styleIdea", "")
        gender = data.get("gender", "1")  # Default: male
        ethnicity = data.get("ethnicity", "")
        age = data.get("age", "")
        skin_color = data.get("skinColor", "")
        season = data.get("season", "")
        accessories = data.get("accessories", "1")  # 1 = with accessories, 0 = no accessories
        occasion = data.get("occasion", "")

        # Ensure required fields are provided
        required_fields = ["styleIdea", "gender", "ethnicity", "age", "skinColor", "season", "accessories", "occasion"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Process gender & accessories input
        accessories = "" if accessories == "1" else "no"
        gender_text = "male" if gender == "1" else "female"

        # Generate text prompt
        prompt = f"a complete {ethnicity} attire for {gender_text} of age {age} skin color {skin_color} to be worn in {season} season with {accessories} accessories to be worn on {occasion} occasion considering the design idea {style_idea}"

        # Generate text description using Google Generative AI
        text_output = generate_output(MODEL_NAME, prompt)

        # Prepare image prompt
        image_prompt = f"Full body image of a {skin_color} skinned {gender_text} model of age {age} wearing {text_output} facing the camera"

        # Generate image using Hugging Face InferenceClient
        image = generate_image(image_prompt)

        # Save image temporarily
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        image_path = 'static/generated/outfit.png'
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        with open(image_path, 'wb') as f:
            f.write(img_byte_arr)

        # Return full URL of the image
        image_url = request.host_url + 'static/generated/outfit.png'

        return jsonify({'image': image_url, 'text': text_output})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
