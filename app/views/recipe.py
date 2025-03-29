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
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    cuisine = request.args.get('cuisine')
    difficulty_values = request.args.getlist('difficulty')
    tags = request.args.getlist('tag')
    cooking_time_max = request.args.get('cooking_time_max')
    filters = {}
    if cuisine:
        filters['cuisine'] = cuisine
    if difficulty_values:
        filters['difficulty'] = {"$in": difficulty_values}
    if tags:
        filters['tags'] = {"$in": tags}
    if cooking_time_max and cooking_time_max.isdigit():
        filters['cooking_time'] = {"$lte": int(cooking_time_max)}
    result = recipe_service.search_recipes(
        query=query,
        filters=filters,
        page=page,
        page_size=12
    )
    template_filters = {
        'cuisine': cuisine,
        'difficulty': difficulty_values or [],
        'tags': tags or [],
        'cooking_time_max': int(cooking_time_max) if cooking_time_max and cooking_time_max.isdigit() else None
    }
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
    similar_recipes = recipe_service.get_similar_recipes(recipe_id, limit=3)
    return render_template('recipes/detail.html', recipe=recipe, similar_recipes=similar_recipes)

@recipe_bp.route('/create', methods=['GET', 'POST'])
def create_recipe():
    """Create new recipe"""
    if request.method == 'POST':
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
                "calories": int(request.form.get('calories', 0) or 0),
                "protein": int(request.form.get('protein', 0) or 0),
                "carbs": int(request.form.get('carbs', 0) or 0),
                "fat": int(request.form.get('fat', 0) or 0)
            },
            "image_url": request.form.get('image_url')
        }
        tags = request.form.get('tags', '').split(',')
        dietary_tags = request.form.getlist('dietary_tags')
        all_tags = [tag.strip() for tag in tags if tag.strip()]
        all_tags.extend(dietary_tags)
        form_data['tags'] = all_tags
        if 'user_id' in session:
            form_data['user_id'] = session['user_id']
            print(f"Setting user_id to {session['user_id']} for new recipe")
        recipe_id = recipe_service.create_recipe(form_data)
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
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
                "calories": int(request.form.get('calories', 0) or 0),
                "protein": int(request.form.get('protein', 0) or 0),
                "carbs": int(request.form.get('carbs', 0) or 0),
                "fat": int(request.form.get('fat', 0) or 0)
            },
            "image_url": request.form.get('image_url')
        }
        tags = request.form.get('tags', '').split(',')
        dietary_tags = request.form.getlist('dietary_tags')
        all_tags = [tag.strip() for tag in tags if tag.strip()]
        all_tags.extend(dietary_tags)
        form_data['tags'] = all_tags
        recipe_service.update_recipe(recipe_id, form_data)
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
    return render_template('recipes/edit.html', recipe=recipe)

@recipe_bp.route('/<recipe_id>/delete', methods=['GET', 'DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe"""
    if 'user_id' not in session:
        if request.method == 'DELETE':
            return jsonify({"status": "error", "message": "Not authorized"}), 401
        return redirect(url_for('user.login'))
    
    try:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if not recipe:
            abort(404)
        if str(recipe.user_id) != session['user_id']:
            if request.method == 'DELETE':
                return jsonify({"status": "error", "message": "Not authorized"}), 403
            return redirect(url_for('recipe.list_recipes'))
        success = recipe_service.delete_recipe(recipe_id)
        if request.method == 'DELETE':
            return jsonify({"status": "success" if success else "error"})
        return redirect(url_for('recipe.list_recipes'))
    except bson_errors.InvalidId:
        if request.method == 'DELETE':
            return jsonify({"status": "error", "message": "Recipe not found"}), 404
        abort(404)


@recipe_bp.route('/<recipe_id>', methods=['DELETE'])
def api_delete_recipe(recipe_id):
    """Delete a recipe (API method)"""
    return delete_recipe(recipe_id)


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
    if 'user_id' not in session:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        return redirect(url_for('user.login'))
    if request.headers.get('Content-Type') == 'application/json':
        data = request.json
        comment_text = data.get('text')
    else:
        comment_text = request.form.get('comment')
    
    if not comment_text or comment_text.strip() == '':
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"status": "error", "message": "Comment text is required"}), 400
        return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))
    user_id = session['user_id']
    username = "User"
    from app.services.user_service import UserService
    user_service = UserService()
    user = user_service.get_user_by_id(user_id)
    if user:
        username = user.username
    comment_data = {
        "user_id": user_id,
        "username": username,
        "text": comment_text,
        "date": datetime.utcnow()
    }
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
    return redirect(url_for('recipe.get_recipe', recipe_id=recipe_id))