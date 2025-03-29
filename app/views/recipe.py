from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, session
from bson import ObjectId, errors as bson_errors
from datetime import datetime
from app.services.recipe_service import RecipeService
from app.models.recipe import Recipe

recipe_bp = Blueprint('recipe', __name__)
recipe_service = RecipeService()

@recipe_bp.route('/')
def list_recipes():
    """List recipes with search and filtering"""
    # Get query parameters
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    cuisine = request.args.get('cuisine')
    difficulty_values = request.args.getlist('difficulty')
    tags = request.args.getlist('tag')
    cooking_time_max = request.args.get('cooking_time_max')
    
    # Build filters
    filters = {}
    if cuisine:
        filters['cuisine'] = cuisine
    if difficulty_values:
        filters['difficulty'] = {"$in": difficulty_values}
    if tags:
        filters['tags'] = {"$in": tags}
    if cooking_time_max and cooking_time_max.isdigit():
        filters['cooking_time'] = {"$lte": int(cooking_time_max)}
    
    # Get recipes
    result = recipe_service.search_recipes(
        query=query,
        filters=filters,
        page=page,
        page_size=12  # 12 recipes per page for grid layout
    )
    
    # For API mode
    if request.headers.get('Accept') == 'application/json':
        # Convert Recipe objects to dictionaries
        recipes_dict = [recipe.to_api_dict() for recipe in result['recipes']]
        return jsonify({
            "recipes": recipes_dict,
            "pagination": result['pagination']
        })
    
    # For web interface - ensure filters is a dict with lists for multi-select items
    template_filters = {
        'cuisine': cuisine,
        'difficulty': difficulty_values or [],  # Ensure this is always a list
        'tags': tags or [],  # Ensure this is always a list
        'cooking_time_max': int(cooking_time_max) if cooking_time_max and cooking_time_max.isdigit() else None
    }
    
    # Return template with data
    return render_template(
        'recipes/list.html',
        recipes=result['recipes'],
        pagination=result['pagination'],
        query=query,
        filters=template_filters
    )

@recipe_bp.route('/<recipe_id>')
def get_recipe(recipe_id):
    """Get single recipe details"""
    try:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
    except bson_errors.InvalidId:
        abort(404)
        
    if not recipe:
        abort(404)
    
    # Get similar recipes
    similar_recipes = recipe_service.get_similar_recipes(recipe_id, limit=3)
    
    # For API mode
    if request.headers.get('Accept') == 'application/json':
        response_data = recipe.to_api_dict()
        response_data['similar_recipes'] = [r.to_api_dict() for r in similar_recipes]
        return jsonify(response_data)
    
    # For web interface
    return render_template('recipes/detail.html', recipe=recipe, similar_recipes=similar_recipes)

@recipe_bp.route('/create', methods=['GET', 'POST'])
def create_recipe():
    """Create new recipe"""
    if request.method == 'POST':
        # For API mode
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            recipe_id = recipe_service.create_recipe(data)
            return jsonify({
                "status": "success",
                "recipe_id": recipe_id
            }), 201
        
        # For web form submission
        form_data = {
            "name": request.form.get('name'),
            "ingredients": [
                {"name": ing_name, "quantity": ing_qty}
                for ing_name, ing_qty in zip(
                    request.form.getlist('ingredient_name[]'),
                    request.form.getlist('ingredient_quantity[]')
                )
            ],
            "instructions": request.form.get('instructions').split('\n'),
            "cuisine": request.form.get('cuisine'),
            "difficulty": request.form.get('difficulty'),
            "preparation_time": int(request.form.get('preparation_time')),
            "cooking_time": int(request.form.get('cooking_time')),
            "nutritional_info": {
                "calories": int(request.form.get('calories', 0)),
                "protein": int(request.form.get('protein', 0)),
                "carbs": int(request.form.get('carbs', 0)),
                "fat": int(request.form.get('fat', 0))
            },
            "tags": request.form.get('tags').split(','),
            "image_url": request.form.get('image_url')
        }
        
        # Handle user_id if logged in
        if 'user_id' in session:
            form_data['user_id'] = session['user_id']
            print(f"Setting user_id to {session['user_id']} for new recipe")
        
        recipe_id = recipe_service.create_recipe(form_data)
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
    
    # GET request - render the form
    return render_template('recipes/create.html')

@recipe_bp.route('/<recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """Edit existing recipe"""
    try:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
    except bson_errors.InvalidId:
        abort(404)
        
    if not recipe:
        abort(404)
    
    if request.method == 'POST':
        # For API mode
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            success = recipe_service.update_recipe(recipe_id, data)
            return jsonify({
                "status": "success" if success else "error"
            })
        
        # For web form submission
        form_data = {
            "name": request.form.get('name'),
            "ingredients": [
                {"name": ing_name, "quantity": ing_qty}
                for ing_name, ing_qty in zip(
                    request.form.getlist('ingredient_name[]'),
                    request.form.getlist('ingredient_quantity[]')
                )
            ],
            "instructions": request.form.get('instructions').split('\n'),
            "cuisine": request.form.get('cuisine'),
            "difficulty": request.form.get('difficulty'),
            "preparation_time": int(request.form.get('preparation_time')),
            "cooking_time": int(request.form.get('cooking_time')),
            "nutritional_info": {
                "calories": int(request.form.get('calories', 0)),
                "protein": int(request.form.get('protein', 0)),
                "carbs": int(request.form.get('carbs', 0)),
                "fat": int(request.form.get('fat', 0))
            },
            "tags": request.form.get('tags').split(','),
            "image_url": request.form.get('image_url')
        }
        
        recipe_service.update_recipe(recipe_id, form_data)
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
    
    # GET request - render the form with current data
    return render_template('recipes/edit.html', recipe=recipe)

@recipe_bp.route('/<recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe"""
    try:
        success = recipe_service.delete_recipe(recipe_id)
    except bson_errors.InvalidId:
        abort(404)
    
    if not success:
        abort(404)
    
    return jsonify({"status": "success"}), 200

@recipe_bp.route('/cuisines')
def list_cuisines():
    """Get list of available cuisines"""
    pipeline = [
        {"$group": {"_id": "$cuisine"}},
        {"$sort": {"_id": 1}}
    ]
    cuisines = [doc["_id"] for doc in recipe_service.collection.aggregate(pipeline)]
    
    return jsonify(cuisines)

@recipe_bp.route('/tags')
def list_tags():
    """Get list of available tags"""
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags"}},
        {"$sort": {"_id": 1}}
    ]
    tags = [doc["_id"] for doc in recipe_service.collection.aggregate(pipeline)]
    
    return jsonify(tags)

@recipe_bp.route('/<recipe_id>/comments', methods=['POST'])
def add_comment(recipe_id):
    """Add a comment to a recipe"""
    # Check if user is logged in
    if 'user_id' not in session:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        return redirect(url_for('user.login'))
    
    # Get the comment data
    if request.headers.get('Content-Type') == 'application/json':
        data = request.json
        comment_text = data.get('text')
    else:
        comment_text = request.form.get('comment')
    
    if not comment_text or comment_text.strip() == '':
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": "Comment text is required"}), 400
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
    
    # Get user info
    user_id = session['user_id']
    username = "User"  # Default username
    
    # Try to get actual username if possible
    from app.services.user_service import UserService
    user_service = UserService()
    user = user_service.get_user_by_id(user_id)
    if user:
        username = user.username
    
    # Create comment data
    comment_data = {
        "user_id": user_id,
        "username": username,
        "text": comment_text,
        "date": datetime.utcnow()
    }
    
    # Add comment directly using PyMongo
    from app import mongo
    result = mongo.db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$push": {"comments": comment_data}}
    )
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "status": "success" if result.modified_count > 0 else "error",
            "comment": {
                "user_id": user_id,
                "username": username,
                "text": comment_text,
                "date": comment_data['date'].isoformat()
            }
        })
    
    # Redirect back to recipe page
    return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))