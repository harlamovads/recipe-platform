import os
import sys
import random
from datetime import datetime

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, mongo
from app.models.recipe import Recipe
from app.models.user import User

def seed_data():
    """Seed database with sample data"""
    app = create_app('development')
    
    with app.app_context():
        print("Clearing existing data...")
        mongo.db.recipes.delete_many({})
        mongo.db.users.delete_many({})
        
        print("Creating sample users...")
        users = create_sample_users()
        user_ids = [user._id for user in users]
        
        print("Creating sample recipes...")
        create_sample_recipes(user_ids)
        
        print("Data seeding complete!")

def create_sample_users():
    """Create sample user accounts"""
    sample_users = [
        {
            "username": "chef_john",
            "email": "john@example.com",
            "password": "password123",
            "dietary_preferences": ["vegetarian"],
            "favorite_cuisines": ["Italian", "Mexican"],
            "cooking_skill_level": "Advanced"
        },
        {
            "username": "foodie_sara",
            "email": "sara@example.com",
            "password": "password123",
            "dietary_preferences": ["gluten-free", "dairy-free"],
            "favorite_cuisines": ["Japanese", "Thai"],
            "cooking_skill_level": "Intermediate"
        },
        {
            "username": "beginner_cook",
            "email": "beginner@example.com",
            "password": "password123",
            "dietary_preferences": [],
            "favorite_cuisines": ["American"],
            "cooking_skill_level": "Beginner"
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        # Hash the password
        password = user_data.pop('password')
        user_data['password_hash'] = User.hash_password(password)
        
        # Create user
        user = User(**user_data)
        mongo.db.users.insert_one(user.to_dict())
        created_users.append(user)
        print(f"Created user: {user.username}")
    
    return created_users

def create_sample_recipes(user_ids):
    """Create sample recipes"""
    sample_recipes = [
        {
            "name": "Classic Spaghetti Carbonara",
            "ingredients": [
                {"name": "Spaghetti", "quantity": "400g"},
                {"name": "Pancetta", "quantity": "150g"},
                {"name": "Egg yolks", "quantity": "4"},
                {"name": "Parmesan cheese", "quantity": "50g"},
                {"name": "Black pepper", "quantity": "1 tsp"},
                {"name": "Salt", "quantity": "to taste"}
            ],
            "instructions": [
                "Bring a large pot of salted water to boil and cook spaghetti according to package instructions.",
                "While pasta cooks, heat a large skillet and cook pancetta until crispy.",
                "In a bowl, whisk together egg yolks and grated cheese.",
                "Drain pasta, reserving 1/2 cup pasta water.",
                "Working quickly, add hot pasta to the skillet with pancetta, then remove from heat.",
                "Pour egg mixture over pasta and toss quickly. Add pasta water as needed to create a creamy sauce.",
                "Season with black pepper and serve immediately."
            ],
            "cuisine": "Italian",
            "difficulty": "Medium",
            "preparation_time": 10,
            "cooking_time": 15,
            "nutritional_info": {
                "calories": 550,
                "protein": 22,
                "carbs": 58,
                "fat": 25
            },
            "tags": ["pasta", "quick-meal", "classic"]
        },
        {
            "name": "Vegetarian Buddha Bowl",
            "ingredients": [
                {"name": "Quinoa", "quantity": "100g"},
                {"name": "Sweet potato", "quantity": "1 medium"},
                {"name": "Chickpeas", "quantity": "400g can"},
                {"name": "Avocado", "quantity": "1"},
                {"name": "Kale", "quantity": "2 cups"},
                {"name": "Tahini", "quantity": "2 tbsp"},
                {"name": "Lemon juice", "quantity": "1 tbsp"},
                {"name": "Olive oil", "quantity": "2 tbsp"},
                {"name": "Cumin", "quantity": "1 tsp"},
                {"name": "Salt and pepper", "quantity": "to taste"}
            ],
            "instructions": [
                "Preheat oven to 200°C/400°F.",
                "Cook quinoa according to package instructions.",
                "Dice sweet potato, toss with olive oil, cumin, salt and pepper, and roast for 25 minutes.",
                "Drain chickpeas, toss with olive oil and spices, and roast for 15 minutes until crispy.",
                "Wash and chop kale, massage with olive oil and lemon juice.",
                "Make dressing by mixing tahini, lemon juice, water, and salt.",
                "Assemble bowl with quinoa, roasted vegetables, chickpeas, kale, and sliced avocado.",
                "Drizzle with tahini dressing and serve."
            ],
            "cuisine": "International",
            "difficulty": "Easy",
            "preparation_time": 15,
            "cooking_time": 30,
            "nutritional_info": {
                "calories": 480,
                "protein": 15,
                "carbs": 45,
                "fat": 28
            },
            "tags": ["vegetarian", "healthy", "bowl", "gluten-free"]
        },
        {
            "name": "Classic Beef Burger",
            "ingredients": [
                {"name": "Ground beef", "quantity": "500g"},
                {"name": "Onion", "quantity": "1 small"},
                {"name": "Garlic", "quantity": "2 cloves"},
                {"name": "Egg", "quantity": "1"},
                {"name": "Breadcrumbs", "quantity": "1/4 cup"},
                {"name": "Worcestershire sauce", "quantity": "1 tbsp"},
                {"name": "Salt and pepper", "quantity": "to taste"},
                {"name": "Burger buns", "quantity": "4"},
                {"name": "Cheese slices", "quantity": "4"},
                {"name": "Lettuce", "quantity": "4 leaves"},
                {"name": "Tomato", "quantity": "1, sliced"},
                {"name": "Red onion", "quantity": "1/2, sliced"},
                {"name": "Ketchup and mustard", "quantity": "to serve"}
            ],
            "instructions": [
                "Finely chop onion and garlic.",
                "In a large bowl, combine ground beef, onion, garlic, egg, breadcrumbs, Worcestershire sauce, salt, and pepper.",
                "Divide mixture into 4 equal portions and shape into patties.",
                "Heat a grill or skillet over medium-high heat.",
                "Cook patties for 4-5 minutes per side, or until desired doneness.",
                "Add cheese slices during the last minute of cooking.",
                "Toast burger buns lightly.",
                "Assemble burgers with lettuce, tomato, onion, and condiments of choice."
            ],
            "cuisine": "American",
            "difficulty": "Easy",
            "preparation_time": 15,
            "cooking_time": 15,
            "nutritional_info": {
                "calories": 650,
                "protein": 32,
                "carbs": 35,
                "fat": 42
            },
            "tags": ["beef", "burger", "classic", "dinner"]
        },
        {
            "name": "Thai Green Curry",
            "ingredients": [
                {"name": "Green curry paste", "quantity": "3 tbsp"},
                {"name": "Coconut milk", "quantity": "400ml can"},
                {"name": "Chicken breast", "quantity": "500g"},
                {"name": "Bamboo shoots", "quantity": "120g"},
                {"name": "Bell pepper", "quantity": "1"},
                {"name": "Snow peas", "quantity": "100g"},
                {"name": "Fish sauce", "quantity": "1 tbsp"},
                {"name": "Palm sugar", "quantity": "1 tbsp"},
                {"name": "Thai basil leaves", "quantity": "handful"},
                {"name": "Jasmine rice", "quantity": "300g"}
            ],
            "instructions": [
                "Slice chicken breast into thin strips.",
                "Heat a wok or large pan over medium-high heat and add 2 tbsp of coconut milk.",
                "Add curry paste and stir-fry until fragrant, about 1 minute.",
                "Add chicken and stir-fry until no longer pink.",
                "Pour in remaining coconut milk, bring to a simmer.",
                "Add bamboo shoots, bell pepper, and snow peas. Cook for 5 minutes.",
                "Season with fish sauce and palm sugar, adjusting to taste.",
                "Stir in Thai basil leaves just before serving.",
                "Serve hot with jasmine rice."
            ],
            "cuisine": "Thai",
            "difficulty": "Medium",
            "preparation_time": 15,
            "cooking_time": 20,
            "nutritional_info": {
                "calories": 520,
                "protein": 28,
                "carbs": 45,
                "fat": 25
            },
            "tags": ["curry", "thai", "chicken", "spicy"]
        },
        {
            "name": "Chocolate Chip Cookies",
            "ingredients": [
                {"name": "Butter", "quantity": "225g"},
                {"name": "Brown sugar", "quantity": "150g"},
                {"name": "White sugar", "quantity": "100g"},
                {"name": "Eggs", "quantity": "2"},
                {"name": "Vanilla extract", "quantity": "1 tsp"},
                {"name": "All-purpose flour", "quantity": "280g"},
                {"name": "Baking soda", "quantity": "1 tsp"},
                {"name": "Salt", "quantity": "1/2 tsp"},
                {"name": "Chocolate chips", "quantity": "300g"}
            ],
            "instructions": [
                "Preheat oven to 175°C/350°F.",
                "In a large bowl, cream together butter and both sugars until smooth.",
                "Beat in eggs one at a time, then stir in vanilla.",
                "In a separate bowl, combine flour, baking soda, and salt.",
                "Gradually blend dry ingredients into the wet mixture.",
                "Fold in chocolate chips.",
                "Drop by rounded tablespoons onto ungreased baking sheets.",
                "Bake for 10-12 minutes or until edges are nicely browned.",
                "Allow cookies to cool on baking sheet for 5 minutes before transferring to a wire rack."
            ],
            "cuisine": "American",
            "difficulty": "Easy",
            "preparation_time": 15,
            "cooking_time": 12,
            "nutritional_info": {
                "calories": 220,
                "protein": 2,
                "carbs": 28,
                "fat": 12
            },
            "tags": ["dessert", "baking", "cookies", "chocolate"]
        }
    ]
    
    for recipe_data in sample_recipes:
        # Add random user as creator
        recipe_data['user_id'] = random.choice(user_ids)
        # Add timestamps
        now = datetime.utcnow()
        recipe_data['created_at'] = now
        recipe_data['updated_at'] = now
        # Create recipe
        recipe = Recipe(**recipe_data)
        result = mongo.db.recipes.insert_one(recipe.to_dict())
        print(f"Created recipe: {recipe.name}")
        # Dunno where to put it, randomize
        num_ratings = random.randint(3, 10)
        ratings = []
        for _ in range(num_ratings):
            ratings.append({
                "user_id": random.choice(user_ids),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "date": datetime.utcnow()
            })
        
        mongo.db.recipes.update_one(
            {"_id": result.inserted_id},
            {"$set": {"user_ratings": ratings}}
        )
    
    # Add some recipes to user favorites
    recipe_ids = [str(r["_id"]) for r in mongo.db.recipes.find({}, {"_id": 1})]
    
    for user_id in user_ids:
        # Randomly select 1-3 recipes as favorites
        num_favorites = random.randint(1, 3)
        favorite_ids = random.sample(recipe_ids, num_favorites)
        
        # Convert to ObjectId
        favorite_object_ids = [ObjectId(rid) for rid in favorite_ids]
        
        # Update user
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"favorite_recipes": favorite_object_ids}}
        )
        print(f"Added {num_favorites} favorites to user {user_id}")

if __name__ == "__main__":
    from bson import ObjectId
    print("Starting data seeding...")
    seed_data()