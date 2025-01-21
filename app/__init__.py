from flask import Flask, render_template, jsonify, request, redirect, send_file
from flask_cors import CORS
import wikipedia
from openai import OpenAI
import os
import re
import datetime as import_datetime
from pathlib import Path

def create_app(api_key=None):
    app = Flask(__name__)
    # Enable CORS with more specific settings
    CORS(app, resources={
        r"/search": {"origins": "*", "methods": ["GET", "OPTIONS"]},
        r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}
    })
    
    # Initialize OpenAI client with provided key or environment variable
    api_key = api_key or os.getenv('OPENAI_API_KEY')
    
    try:
        client = OpenAI(api_key=api_key) if api_key else None
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")
        client = None
    
    # Ensure the audio directory exists
    audio_dir = Path(app.root_path) / "static" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/search', methods=['GET', 'OPTIONS'])
    def search():
        if request.method == 'OPTIONS':
            return '', 204
            
        query = request.args.get('query', '')
        print(f"Received search request for query: {query}")  # Debug log
        
        if not query:
            print("No query provided")  # Debug log
            return jsonify({'results': [], 'error': 'No search query provided'}), 400
            
        try:
            # Search Wikipedia with more results to improve relevance
            print(f"Searching Wikipedia for: {query}")  # Debug log
            search_results = wikipedia.search(query, results=10)
            results = []
            
            print(f"Found {len(search_results)} initial results")  # Debug log
            
            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    # Ensure summary is a string and not too long
                    summary = page.summary if page.summary else ""
                    if len(summary) > 500:  # Limit summary length
                        summary = summary[:500] + "..."
                    
                    # Calculate relevance score based on title match
                    relevance = 0
                    if query.lower() in title.lower():
                        relevance += 2
                        if query.lower() == title.lower():
                            relevance += 3
                        
                    results.append({
                        'title': page.title or "",
                        'summary': summary,
                        'url': page.url or "#",
                        'id': str(hash(page.url)),  # Add a unique ID for each result
                        'relevance': relevance
                    })
                except wikipedia.exceptions.DisambiguationError as e:
                    print(f"Disambiguation error for {title}")  # Debug log
                    continue
                except wikipedia.exceptions.PageError:
                    print(f"Page error for {title}")  # Debug log
                    continue
                except Exception as e:
                    print(f"Error processing {title}: {str(e)}")  # Debug log
                    continue
            
            # Sort results by relevance score
            results.sort(key=lambda x: x['relevance'], reverse=True)
            # Remove relevance score from output
            for result in results:
                del result['relevance']
            
            final_results = results[:5]  # Return top 5 most relevant results
            print(f"Returning {len(final_results)} results")  # Debug log
            
            response = jsonify({
                'results': final_results,
                'query': query,
                'timestamp': import_datetime.datetime.now().isoformat()
            })
            
            # Add CORS headers explicitly
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
            
            return response
            
        except Exception as e:
            print(f"Search error: {str(e)}")  # Debug log
            return jsonify({'error': str(e), 'results': []}), 500
    
    @app.route('/api/wiki', methods=['GET'])
    def wiki_search():
        query = request.args.get('q', '')
        return redirect(f"/search?query={query}")
            
    @app.route('/api/summarize', methods=['POST', 'OPTIONS'])
    def summarize_text():
        if request.method == 'OPTIONS':
            return '', 204
            
        try:
            if not client:
                return jsonify({'error': 'OpenAI API key not configured or invalid'}), 500
                
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data received'}), 400
                
            text = data.get('text', '')
            
            if not text:
                return jsonify({'error': 'No text provided'}), 400
            
            try:
                # Call OpenAI API for summarization
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                        {"role": "user", "content": f"Please provide a concise summary of the following text:\n\n{text}"}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                # Ensure we return a valid string
                summary = response.choices[0].message.content if response.choices else ""
                return jsonify({'summary': summary or "No summary available"})
            except Exception as e:
                return jsonify({'error': f'OpenAI API error: {str(e)}'}), 500
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/speak', methods=['POST'])
    def text_to_speech():
        try:
            if not client:
                return jsonify({'error': 'OpenAI API key not configured or invalid'}), 500

            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({'error': 'No text provided'}), 400

            text = data['text']
            
            # Generate a unique filename for this speech
            timestamp = import_datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"speech_{timestamp}.mp3"
            speech_file_path = audio_dir / filename

            # Create the speech file using OpenAI's TTS
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )

            # Save the audio file
            response.stream_to_file(str(speech_file_path))

            # Return the URL to the audio file
            return jsonify({
                'audio_url': f"/static/audio/{filename}",
                'message': 'Speech generated successfully'
            })

        except Exception as e:
            print(f"TTS error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return app 