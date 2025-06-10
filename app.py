import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import markdown 

app = Flask(__name__)
CORS(app)

GOOGLE_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"  

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_ACTUAL_GEMINI_API_KEY_HERE":
    raise ValueError("Please replace 'YOUR_ACTUAL_GEMINI_API_KEY_HERE' with your actual Google Gemini API key in app.py")

genai.configure(api_key=GOOGLE_API_KEY)

model = None

def get_available_text_model():
    print("Checking for available Gemini models...")

    for m in genai.list_models():
        if m.name == 'models/gemini-1.5-flash' and 'generateContent' in m.supported_generation_methods:
            print(f"Prioritizing recommended model: {m.name}")
            return genai.GenerativeModel(m.name)
            
    for m in genai.list_models():
        if m.name == 'models/gemini-1.0-pro' and 'generateContent' in m.supported_generation_methods:
            print(f"Falling back to suitable text model: {m.name}")
            return genai.GenerativeModel(m.name)
            
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Using general suitable model: {m.name}")
            return genai.GenerativeModel(m.name)
            
    raise Exception("No Gemini model found that supports 'generateContent'. Please ensure your API key is correct and valid, or check Google AI Studio for available models.")

with app.app_context():
    try:
        model = get_available_text_model()
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Gemini model: {e}")
        print("Exiting application. Please check your API key and network connection.")
        exit()

def explain_sql_query_llm(sql_query):
    if not sql_query.strip():
        return "Please enter a SQL query to explain."

    prompt = f"""
    You are an expert SQL data engineer. Explain the following SQL query in simple, clear, and natural language.
    Break down its purpose, what each main clause does (e.g., SELECT, FROM, JOIN, WHERE, GROUP BY, ORDER BY),
    and explain any complex functions or subqueries. Please use Markdown formatting for headings, bold text, and bullet points to make the explanation easy to read.
    
    SQL Query:
    ```sql
    {sql_query}
    ```
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip() 
        html_explanation = markdown.markdown(raw_text) 
        return html_explanation

    except Exception as e:
        return f"An error occurred during content generation: {e}. The model might have encountered an issue or you hit a rate limit."


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/explain', methods=['POST'])
def explain():
    data = request.get_json()
    sql_query = data.get('sql_query', '')

    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    explanation = explain_sql_query_llm(sql_query)
    
    if explanation.startswith("An error occurred during content generation:"):
        return jsonify({'error': explanation}), 500
    
    return jsonify({'explanation': explanation}) 

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open your browser and navigate to: http://127.0.0.1:5000/")
    app.run(debug=True)