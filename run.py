from app import create_app
import sys
import os
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if API key is provided as command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv('OPENAI_API_KEY')
    
    app = create_app(api_key=api_key)
    app.run(debug=True, port=5003)

if __name__ == '__main__':
    main() 