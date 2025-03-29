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
            return render_template('users/register.html', error=result['message'], form_data=form_data)
    return render_template('users/register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = user_service.authenticate_user(username, password)
        if user:
            session['user_id'] = user._id
            return redirect(url_for('main.index'))
        else:
            return render_template('users/login.html', error="Invalid credentials")
    return render_template('users/login.html')

@user_bp.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

@user_bp.route('/profile')
def user_profile():
    """User profile page"""
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    user = user_service.get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    user_recipes = recipe_service.get_user_recipes(user._id, page=1, page_size=4)
    comment_count = recipe_service.count_user_comments(user._id)
    favorite_recipes = []
    for recipe_id in user.favorite_recipes[:4]:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if recipe:
            favorite_recipes.append(recipe)
    user_profile = user_service.get_recommendation_profile(user._id)
    recommended_recipes = []
    if user_profile:
        pipeline = [
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
            {"$sort": {"recommendationScore": -1}},
            {"$limit": 2}
        ]
        if not user_profile.get('dietary_preferences') and not user_profile.get('favorite_cuisines'):
            pipeline.pop(0)
        recommended_docs = list(recipe_service.collection.aggregate(pipeline))
        recommended_recipes = [Recipe.from_dict(doc) for doc in recommended_docs]
    return render_template('users/profile.html', 
                          user=user, 
                          user_recipes=user_recipes, 
                          comment_count=comment_count,
                          recommended_recipes=recommended_recipes,
                          favorite_recipes=favorite_recipes)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    if request.method == 'POST':
        form_data = {
            'email': request.form.get('email'),
            'dietary_preferences': request.form.getlist('dietary_preferences'),
            'favorite_cuisines': request.form.getlist('favorite_cuisines'),
            'cooking_skill_level': request.form.get('cooking_skill_level')
        }
        if request.form.get('new_password'):
            form_data['password'] = request.form.get('new_password')
        success = user_service.update_user(user_id, form_data)
        if success:
            return redirect(url_for('user.user_profile'))
        else:
            return render_template('users/edit_profile.html', 
                                  user=user, 
                                  error="Failed to update profile")
    return render_template('users/edit_profile.html', user=user)

@user_bp.route('/favorites')
def favorites():
    """Show user's favorite recipes"""
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('user.login'))
    favorite_ids = user.favorite_recipes
    favorite_recipes = []
    for recipe_id in favorite_ids:
        recipe = recipe_service.get_recipe_by_id(recipe_id)
        if recipe:
            favorite_recipes.append(recipe)
    return render_template('users/favorites.html', recipes=favorite_recipes)

@user_bp.route('/recipes/<recipe_id>/favorite', methods=['POST'])
def add_favorite(recipe_id):
    """Add a recipe to user's favorites"""
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
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    user_id = session['user_id']
    user = user_service.get_user_by_id(user_id)
    user_profile = user_service.get_recommendation_profile(user_id)
    if not user_profile:
        return jsonify({"status": "error", "message": "User not found"}), 404
    page = int(request.args.get('page', 1))
    page_size = 12
    pipeline = [
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
        {"$sort": {"recommendationScore": -1}},
        {"$skip": (page - 1) * page_size},
        {"$limit": page_size}
    ]
    if not user_profile.get('dietary_preferences') and not user_profile.get('favorite_cuisines'):
        pipeline.pop(0)
    recommended_recipes = list(recipe_service.collection.aggregate(pipeline))
    recipes = [Recipe.from_dict(doc) for doc in recommended_recipes]
    count_pipeline = pipeline.copy()
    if len(count_pipeline) > 3:
        count_pipeline = count_pipeline[:-2]
    count_pipeline.append({"$count": "total"})
    count_result = list(recipe_service.collection.aggregate(count_pipeline))
    total_items = count_result[0]['total'] if count_result else 0
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages
    }
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