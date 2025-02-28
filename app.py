from flask import Flask, request, jsonify, render_template, send_file
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
    style_idea = request.form['styleIdea']
    gender = request.form['gender']
    ethnicity = request.form['ethnicity']
    age = request.form['age']
    skin_color = request.form['skinColor']
    season = request.form['season']
    accessories = request.form['accessories']
    occasion = request.form['occasion']

    # Prepare prompt based on gender
    if accessories == "1":
        accessories = ""
    else:
        accessories = "no"

    if gender == "1":
        gender = "male"
        prompt = f"a complete {ethnicity} attire for male of age {age} skin color {skin_color} to be worn in {season} season with {accessories} accessories to be worn on {occasion} occasion considering the design idea {style_idea}"
    else:
        gender = "female"
        prompt = f"a complete {ethnicity} attire for female of age {age} skin color {skin_color} to be worn in {season} season with {accessories} accessories to be worn on {occasion} occasion considering the design idea {style_idea}"

    # Generate text description using Google Generative AI
    text_output = generate_output(MODEL_NAME, prompt)

    # Prepare image prompt
    if gender == "male":
        image_prompt = f"Full body image of a {skin_color} skinned male model of age {age} wearing {text_output} facing the camera"
    else:
        image_prompt = f"Full body image of a {skin_color} skinned female model of age {age} wearing {text_output} facing the camera"

    # Generate image using Hugging Face InferenceClient
    image = generate_image(image_prompt)

    # Save image temporarily and return URL
    # Note: The image returned by InferenceClient is likely a PIL Image or bytes; assuming it's a PIL Image for consistency
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    image_path = 'static/generated/outfit.png'
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, 'wb') as f:
        f.write(img_byte_arr)

    return jsonify({
        'image': f'/static/generated/outfit.png',
        'text': text_output
    })

if __name__ == '__main__':
    app.run(debug=True)