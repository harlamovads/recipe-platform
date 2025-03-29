import os
from app import create_app
from app.models.recipe import Recipe
from app.models.user import User
from app import mongo

# Get environment configuration
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)