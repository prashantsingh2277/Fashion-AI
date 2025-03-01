from flask import Flask, request, jsonify, send_file
import io
import google.generativeai as genai
from huggingface_hub import InferenceClient
import time
from PIL import Image

app = Flask(__name__)

# Google Generative AI configuration for text generation
def generate_output(model_name, user_input):
    try:
        api_key = "AIzaSyDBH2_fjAeB64R-4uWbwzlCPXb9r8lXujA"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content({"parts": [{"text": user_input}]})
        return response.text.strip()
    except Exception as e:
        return f"Text generation error: {e}"

# Hugging Face configuration for image generation
def generate_image(prompt, model="jbilcke-hf/flux-dev-panorama-lora-2", retries=3, delay=5):
    client = InferenceClient(model, token="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")
    
    for attempt in range(retries):
        try:
            response = client.text_to_image(prompt)
            image = Image.open(io.BytesIO(response))
            return image
        except Exception as e:
            print(f"Image generation attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    raise Exception("Image generation failed after multiple attempts.")

MODEL_NAME = "tunedModels/outfitsuggestiongenerator-usqw4b296kfe"

@app.route('/')
def index():
    return jsonify({"message": "Flask API is running successfully!"})

@app.route('/generate', methods=['POST'])
def generate_outfit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        required_fields = ["styleIdea", "gender", "ethnicity", "age", "skinColor", "season", "accessories", "occasion"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        gender_text = "male" if data["gender"] == "1" else "female"
        accessories_text = "with accessories" if data["accessories"] == "1" else "without accessories"
        
        prompt = (f"A complete {data['ethnicity']} attire for {gender_text}, age {data['age']}, skin color {data['skinColor']}, "
                  f"for the {data['season']} season, {accessories_text}, suitable for a {data['occasion']}, "
                  f"considering the design idea: {data['styleIdea']}")
        
        text_output = generate_output(MODEL_NAME, prompt)
        image_prompt = f"Full-body image of a {gender_text} with {data['skinColor']} skin, age {data['age']}, wearing {text_output}, facing the camera."
        
        image = generate_image(image_prompt)
        
        img_io = io.BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
