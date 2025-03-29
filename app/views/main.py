from flask import Blueprint, render_template, jsonify, request, current_app
from app.services.recipe_service import RecipeService

main_bp = Blueprint('main', __name__)
recipe_service = RecipeService()

@main_bp.route('/')
def index():
    """Homepage route"""
    # Get popular recipes for homepage
    popular_recipes = recipe_service.get_popular_recipes(limit=6)
    
    # For API mode, return JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "popular_recipes": [recipe.to_dict() for recipe in popular_recipes]
        })
    
    # For web interface, render template
    return render_template('index.html', popular_recipes=popular_recipes)

@main_bp.route('/stats')
def stats():
    """Recipe statistics route"""
    recipe_stats = recipe_service.get_recipe_stats()
    
    # For API mode, return JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify(recipe_stats)
    
    # For web interface, render template
    return render_template('stats.html', stats=recipe_stats)

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy"})