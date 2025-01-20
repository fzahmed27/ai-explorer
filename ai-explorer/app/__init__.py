from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    from app import routes
    app.register_blueprint(routes.main)
    
    return app 