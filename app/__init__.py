from flask import Flask
from flask_pymongo import PyMongo
from app.config import config
from bson import ObjectId
import json

# Initialize PyMongo extension
mongo = PyMongo()

# Custom JSON encoder to handle MongoDB ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)

def create_app(config_name='default'):
    """
    Application factory pattern to create Flask app instance
    
    Args:
        config_name (str): Configuration environment
        
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure secret key is set for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-key-for-recipe-platform'
    
    # Custom JSON encoder for MongoDB ObjectId
    app.json_encoder = MongoJSONEncoder
    
    # Initialize extensions
    mongo.init_app(app)
    
    # Register blueprints
    from app.views.main import main_bp
    from app.views.recipe import recipe_bp
    from app.views.user import user_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(recipe_bp, url_prefix='/recipes')
    app.register_blueprint(user_bp, url_prefix='/users')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_template_context(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return {"error": "Internal server error"}, 500

def register_template_context(app):
    """Register context processors for templates."""
    
    @app.context_processor
    def inject_context():
        from datetime import datetime
        return {
            'current_year': datetime.now().year
        }