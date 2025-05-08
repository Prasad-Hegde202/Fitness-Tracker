from flask import Flask
from fitex.extensions import db, login_manager
from fitex.auth.routes import auth_bp  # Import the blueprint

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app