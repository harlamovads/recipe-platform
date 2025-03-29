from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, session
from app.services.user_service import UserService
from app.services.recipe_service import RecipeService
from app.models.user import User
from app.models.recipe import Recipe

user_bp = Blueprint('user', __name__)
user_service = UserService()
recipe_service = RecipeService()

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # For API mode
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            result = user_service.create_user(data)
            return jsonify(result), 201 if result['status'] == 'success' else 400
        
        # For web form submission
        form_data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'dietary_preferences': request.form.getlist('dietary_preferences'),
            'favorite_cuisines': request.form.getlist('favorite_cuisines'),
            'cooking_skill_level': request.form.get('cooking_skill_level', 'Beginner')
        }
        
        result = user_service.create_user(form_data)
        
        if result['status'] == 'success':
            # Set user as logged in
            session['user_id'] = result['user_id']
            return redirect(url_for('main.index'))
        else:
            # Re-render form with error
            return render_template('users/register.html', error=result['message'], form_data=form_data)
    
    # GET request - render the form
    return render_template('users/register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        # For API mode
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            user = user_service.authenticate_user(data['username'], data['password'])
            
            if user:
                # In a real app, generate JWT or other token
                return jsonify({
                    "status": "success",
                    "user_id": user._id
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid credentials"
                }), 401
        
        # For web form submission
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = user_service.authenticate_user(username, password)
        
        if user:
            session['user_id'] = user._id
            return redirect(url_for('main.index'))
        else:
            return render_template('users/login.html', error="Invalid credentials")
    
    # GET request - render the form
    return render_template('users/login.html')

@user_bp.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

@user_bp.route('/profile')
def user_profile():
    """User profile page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    user = user_service.get_user_by_id(session['user_id'])
    
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    
    # Get user's recipes
    user_recipes = recipe_service.get_user_recipes(user._id, page=1, page_size=4)
    
    # Get comment count
    comment_count = recipe_service.count_user_comments(user._id)

    favorite_recipes = []
    for recipe_id in user.favorite_recipes[:4]:  # Limit to 4 for the profile view
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if recipe:
            favorite_recipes.append(recipe)
    
    # Get recommendations
    user_profile = user_service.get_recommendation_profile(user._id)
    recommended_recipes = []
    
    if user_profile:
        pipeline = [
            # Initial stage to match at least one preference if possible
            {"$match": {
                "$or": [
                    {"tags": {"$in": user_profile.get('dietary_preferences', [])}},
                    {"cuisine": {"$in": user_profile.get('favorite_cuisines', [])}},
                    {"difficulty": {"$in": get_difficulty_levels(user_profile.get('cooking_skill_level', 'Beginner'))}}
                ]
            }},
            {"$addFields": {
                "dietaryMatchCount": {
                    "$size": {
                        "$setIntersection": ["$tags", user_profile.get('dietary_preferences', [])]
                    }
                },
                "isFavoriteCuisine": {
                    "$cond": [
                        {"$in": ["$cuisine", user_profile.get('favorite_cuisines', [])]},
                        1,
                        0
                    ]
                },
                "isAppropriateSkillLevel": {
                    "$cond": [
                        {"$in": ["$difficulty", get_difficulty_levels(user_profile.get('cooking_skill_level', 'Beginner'))]},
                        1,
                        0
                    ]
                }
            }},
            {"$addFields": {
                "recommendationScore": {
                    "$add": [
                        "$dietaryMatchCount",
                        "$isFavoriteCuisine",
                        "$isAppropriateSkillLevel"
                    ]
                }
            }},
            # Sort by score (descending)
            {"$sort": {"recommendationScore": -1}},
            # Limit results for profile page
            {"$limit": 2}
        ]
        
        # If no preferences at all, just return popular recipes
        if not user_profile.get('dietary_preferences') and not user_profile.get('favorite_cuisines'):
            # Remove matching stage from pipeline
            pipeline.pop(0)
        
        # Execute pipeline
        recommended_docs = list(recipe_service.collection.aggregate(pipeline))
        
        # Convert to Recipe objects
        recommended_recipes = [Recipe.from_dict(doc) for doc in recommended_docs]
    
    # For API mode
    if request.headers.get('Accept') == 'application/json':
        return jsonify(user.to_api_dict())
    
    # For web interface
    return render_template('users/profile.html', 
                          user=user, 
                          user_recipes=user_recipes, 
                          comment_count=comment_count,
                          recommended_recipes=recommended_recipes,
                          favorite_recipes=favorite_recipes)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    
    if request.method == 'POST':
        # For API mode
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            success = user_service.update_user(user_id, data)
            return jsonify({
                "status": "success" if success else "error"
            })
        
        # For web form submission
        form_data = {
            'email': request.form.get('email'),
            'dietary_preferences': request.form.getlist('dietary_preferences'),
            'favorite_cuisines': request.form.getlist('favorite_cuisines'),
            'cooking_skill_level': request.form.get('cooking_skill_level')
        }
        
        # Handle password update - only if new password is provided
        if request.form.get('new_password'):
            form_data['password'] = request.form.get('new_password')
        
        success = user_service.update_user(user_id, form_data)
        
        if success:
            return redirect(url_for('user.user_profile'))
        else:
            return render_template('users/edit_profile.html', 
                                  user=user, 
                                  error="Failed to update profile")
    
    # GET request - render the form with current data
    return render_template('users/edit_profile.html', user=user)

@user_bp.route('/favorites')
def favorites():
    """Show user's favorite recipes"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    
    # Get favorite recipe IDs
    favorite_ids = user.favorite_recipes
    
    # Get the actual recipe details for each ID
    favorite_recipes = []
    for recipe_id in favorite_ids:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if recipe:
            favorite_recipes.append(recipe)
    
    # For API mode
    if request.headers.get('Accept') == 'application/json':
        return jsonify([recipe.to_api_dict() for recipe in favorite_recipes])
    
    # For web interface
    return render_template('users/favorites.html', recipes=favorite_recipes)

@user_bp.route('/recipes/<recipe_id>/favorite', methods=['POST'])
def add_favorite(recipe_id):
    """Add a recipe to user's favorites"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    user_id = session['user_id']
    
    success = user_service.add_favorite_recipe(user_id, recipe_id)
    
    return jsonify({
        "status": "success" if success else "error"
    })

@user_bp.route('/recipes/<recipe_id>/favorite', methods=['DELETE'])
def remove_favorite(recipe_id):
    """Remove a recipe from user's favorites"""
    # Check if user is logged in
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    user_id = session['user_id']
    
    success = user_service.remove_favorite_recipe(user_id, recipe_id)
    
    return jsonify({
        "status": "success" if success else "error"
    })

@user_bp.route('/recommendations')
def recommendations():
    """Get personalized recipe recommendations"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    
    # Get user preference profile
    user_profile = user_service.get_recommendation_profile(user_id)
    
    if not user_profile:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    # Get page parameter
    page = int(request.args.get('page', 1))
    page_size = 12  # Number of recipes per page
    
    # Generate recommendations using aggregation pipeline for scoring
    pipeline = [
        # Initial stage to match at least one preference if possible
        {"$match": {
            "$or": [
                # Match on dietary preferences if any
                {"tags": {"$in": user_profile.get('dietary_preferences', [])}},
                # Match on favorite cuisines if any
                {"cuisine": {"$in": user_profile.get('favorite_cuisines', [])}},
                # Match on appropriate difficulty based on skill level
                {"difficulty": {"$in": get_difficulty_levels(user_profile.get('cooking_skill_level', 'Beginner'))}}
            ]
        }},
        # Add scoring fields
        {"$addFields": {
            "dietaryMatchCount": {
                "$size": {
                    "$setIntersection": ["$tags", user_profile.get('dietary_preferences', [])]
                }
            },
            "isFavoriteCuisine": {
                "$cond": [
                    {"$in": ["$cuisine", user_profile.get('favorite_cuisines', [])]},
                    1,
                    0
                ]
            },
            "isAppropriateSkillLevel": {
                "$cond": [
                    {"$in": ["$difficulty", get_difficulty_levels(user_profile.get('cooking_skill_level', 'Beginner'))]},
                    1,
                    0
                ]
            }
        }},
        # Calculate total score
        {"$addFields": {
            "recommendationScore": {
                "$add": [
                    "$dietaryMatchCount",
                    "$isFavoriteCuisine",
                    "$isAppropriateSkillLevel"
                ]
            }
        }},
        # Sort by score (descending)
        {"$sort": {"recommendationScore": -1}},
        # Skip for pagination
        {"$skip": (page - 1) * page_size},
        # Limit results
        {"$limit": page_size}
    ]
    
    # If no preferences at all, just return popular recipes
    if not user_profile.get('dietary_preferences') and not user_profile.get('favorite_cuisines'):
        # Remove matching stage from pipeline
        pipeline.pop(0)
    
    # Execute pipeline
    recommended_recipes = list(recipe_service.collection.aggregate(pipeline))
    
    # Convert to Recipe objects
    recipes = [Recipe.from_dict(doc) for doc in recommended_recipes]
    
    # Count total matching recipes for pagination
    count_pipeline = pipeline.copy()
    # Remove pagination stages
    if len(count_pipeline) > 3:  # Make sure we have enough stages to remove
        count_pipeline = count_pipeline[:-2]  # Remove skip and limit
    count_pipeline.append({"$count": "total"})
    
    count_result = list(recipe_service.collection.aggregate(count_pipeline))
    total_items = count_result[0]['total'] if count_result else 0
    
    # Build pagination metadata
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages
    }
    
    # For API mode
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "recipes": [recipe.to_dict() for recipe in recipes],
            "pagination": pagination
        })
    
    # For web interface
    return render_template(
        'users/recommendations.html',
        recipes=recipes,
        pagination=pagination,
        user=user
    )

def get_difficulty_levels(skill_level):
    """Get appropriate difficulty levels based on skill level"""
    skill_to_difficulty = {
        "Beginner": ["Easy"],
        "Intermediate": ["Easy", "Medium"],
        "Advanced": ["Easy", "Medium", "Hard"]
    }
    return skill_to_difficulty.get(skill_level, ["Easy"])