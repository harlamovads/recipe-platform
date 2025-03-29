import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-recipe-platform')
    MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://mongodb:27017/recipe_platform')
    DEBUG = False
    TESTING = False
    
    # MongoDB Collection Names
    RECIPES_COLLECTION = 'recipes'
    USERS_COLLECTION = 'users'
    
    # API settings
    API_TITLE = 'Recipe Discovery Platform API'
    API_VERSION = 'v1'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    # Cache settings
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    MONGO_URI = os.environ.get('TEST_MONGODB_URI', 'mongodb://mongodb:27017/recipe_platform_test')
    
class ProductionConfig(Config):
    """Production environment configuration"""
    # In production, ensure SECRET_KEY is properly set in environment variables
    # and ensure MongoDB connection uses authentication
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}