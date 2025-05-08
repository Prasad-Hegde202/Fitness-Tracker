from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from .fitex import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
     # Register blueprints
     
    from fitex.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    from main import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Import models after db initialization to avoid circular imports
from fitex.models import User

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)