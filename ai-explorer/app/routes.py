from flask import Blueprint, request, jsonify, render_template
import wikipediaapi
import os
from openai import OpenAI
import requests.exceptions
from dotenv import load_dotenv
import openai

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file")

client = OpenAI(api_key=api_key)
print(f"Loaded API key: {api_key[:10]}...")
main = Blueprint('main', __name__)

def get_related_topics(page):
    """Get related topics from a Wikipedia page."""
    related_topics = list(page.links.keys())
    return related_topics[:10]

user_agent = "AI_Explorer/1.0 (https://github.com/fzahmed27/ai-explorer; fzahmed81@gmail.com)"
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent=user_agent,
    timeout=30.0
)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/api/status')
def api_status():
    return jsonify({"message": "Welcome to AI Explorer API"})

@main.route('/main-page')
def main_page():
    try:
        page = wiki_wiki.page('Main Page')
        if page.exists():
            if "may refer to" in page.summary:
                related_topics = get_related_topics(page)
                return jsonify({
                    'title': page.title,
                    'type': 'disambiguation',
                    'message': 'This is a disambiguation page.',
                    'related_topics': related_topics
                })
            return jsonify({
                'title': page.title,
                'summary': page.summary
            })
        return jsonify({'error': 'Could not fetch main page'}), 404
    except requests.exceptions.ReadTimeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/search', methods=['GET', 'POST'])
def search():
    data = request.args.get('query')
    if not data:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    try:
        page = wiki_wiki.page(data)
        if page.exists():
            return jsonify({'page': page.title, 'summary': page.summary})
        else:
            return jsonify({'error': 'Page not found'}), 404
    except requests.exceptions.ReadTimeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/summarize', methods=['GET', 'POST'])
def summarize():
    print("Request received at /summarize")
    print("Request method:", request.method)
    
    # Validate request method
    if request.method != 'POST':
        return jsonify({'error': 'Only POST method is allowed'}), 405
    
    # Validate content type
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    
    print("Request data:", request.get_data())
    print("Request JSON:", request.json)
    
    data = request.json
    if not data:
        print("No JSON data received")
        return jsonify({'error': 'No JSON data received'}), 400
        
    content = data.get('content', '').strip()
    print("Content received:", content)
    
    # Enhanced content validation
    if not content:
        print("Content is required but was not provided")
        return jsonify({'error': 'Please enter some text to summarize'}), 400
    
    if len(content) < 10:
        return jsonify({'error': 'Text must be at least 10 characters long'}), 400
        
    if len(content) > 10000:
        return jsonify({'error': 'Text must not exceed 10,000 characters'}), 400

    try:
        print("Making OpenAI API request...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": content}
            ],
            max_tokens=1000
        )
        summary = response.choices[0].message.content
        print("Summary generated:", summary[:100] + "...")
        return jsonify({'summary': summary})
    except openai.RateLimitError as e:
        print("Rate limit error:", str(e))
        return jsonify({'error': 'OpenAI API quota exceeded. Please try again later or check your API key.'}), 429
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({'error': str(e)}), 500
