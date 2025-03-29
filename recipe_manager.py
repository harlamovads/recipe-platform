import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from typing import List, Dict, Any
import random
import os
import time

class RecipeManager:
    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB connection and database
        
        Args:
            connection_string (str): MongoDB connection string
        """
        # If no connection string is provided, try to get it from environment variable or use default
        if connection_string is None:
            connection_string = os.environ.get('MONGODB_URI', 'mongodb://mongodb:27017/')
        
        # Add retry logic for container startup timing
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                print(f"Attempting to connect to MongoDB at {connection_string} (attempt {attempt+1}/{max_attempts})")
                self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
                # Test the connection
                self.client.admin.command('ping')
                print("Successfully connected to MongoDB")
                break
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                if attempt < max_attempts - 1:
                    sleep_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("Max connection attempts reached. Exiting.")
                    raise
        
        self.db = self.client['recipe_platform']
        self.recipes_collection = self.db['recipes']
        self.users_collection = self.db['users']

    def insert_sample_recipes(self):
        """
        Insert sample recipe data for demonstration
        """
        # Clear existing data
        self.recipes_collection.delete_many({})
        
        sample_recipes = [
            {
                "name": "Vegetarian Pasta",
                "ingredients": [
                    {"name": "Pasta", "quantity": "200g"},
                    {"name": "Tomatoes", "quantity": "2"},
                    {"name": "Basil", "quantity": "10 leaves"}
                ],
                "cuisine": "Italian",
                "difficulty": "Easy",
                "preparation_time": 30,
                "nutritional_info": {
                    "calories": 350,
                    "protein": 12,
                    "carbs": 55
                },
                "tags": ["vegetarian", "quick-meal"],
                "user_ratings": [
                    {"rating": 4.5, "user_id": ObjectId()}
                ]
            },
            {
                "name": "Chicken Curry",
                "ingredients": [
                    {"name": "Chicken", "quantity": "500g"},
                    {"name": "Curry Paste", "quantity": "2 tbsp"},
                    {"name": "Coconut Milk", "quantity": "400ml"}
                ],
                "cuisine": "Indian",
                "difficulty": "Medium",
                "preparation_time": 45,
                "nutritional_info": {
                    "calories": 520,
                    "protein": 32,
                    "carbs": 18
                },
                "tags": ["spicy", "high-protein"],
                "user_ratings": [
                    {"rating": 4.8, "user_id": ObjectId()}
                ]
            },
            {
                "name": "Greek Salad",
                "ingredients": [
                    {"name": "Cucumber", "quantity": "1"},
                    {"name": "Tomatoes", "quantity": "2"},
                    {"name": "Feta Cheese", "quantity": "100g"},
                    {"name": "Olives", "quantity": "50g"},
                    {"name": "Olive Oil", "quantity": "2 tbsp"}
                ],
                "cuisine": "Greek",
                "difficulty": "Easy",
                "preparation_time": 15,
                "nutritional_info": {
                    "calories": 280,
                    "protein": 8,
                    "carbs": 12
                },
                "tags": ["vegetarian", "quick-meal", "low-carb"],
                "user_ratings": [
                    {"rating": 4.2, "user_id": ObjectId()}
                ]
            },
            {
                "name": "Sushi Rolls",
                "ingredients": [
                    {"name": "Sushi Rice", "quantity": "300g"},
                    {"name": "Nori Sheets", "quantity": "5"},
                    {"name": "Salmon", "quantity": "200g"},
                    {"name": "Avocado", "quantity": "1"}
                ],
                "cuisine": "Japanese",
                "difficulty": "Hard",
                "preparation_time": 60,
                "nutritional_info": {
                    "calories": 420,
                    "protein": 22,
                    "carbs": 60
                },
                "tags": ["seafood", "special-occasion"],
                "user_ratings": [
                    {"rating": 4.9, "user_id": ObjectId()}
                ]
            }
        ]
        
        result = self.recipes_collection.insert_many(sample_recipes)
        print(f"Inserted {len(result.inserted_ids)} sample recipes")

    def search_recipes(self, query: Dict[str, Any]) -> List[Dict]:
        """
        Search recipes based on multiple criteria
        
        Args:
            query (dict): Search parameters
        
        Returns:
            List of matching recipes
        """
        return list(self.recipes_collection.find(query))

    def aggregate_recipes_by_cuisine(self) -> List[Dict]:
        """
        Aggregate recipes by cuisine with count
        
        Returns:
            List of cuisine aggregation results
        """
        pipeline = [
            {"$group": {
                "_id": "$cuisine",
                "total_recipes": {"$sum": 1},
                "average_difficulty": {"$avg": {"$switch": {
                    "branches": [
                        {"case": {"$eq": ["$difficulty", "Easy"]}, "then": 1},
                        {"case": {"$eq": ["$difficulty", "Medium"]}, "then": 2},
                        {"case": {"$eq": ["$difficulty", "Hard"]}, "then": 3}
                    ],
                    "default": 0
                }}}
            }},
            {"$sort": {"total_recipes": -1}}
        ]
        return list(self.recipes_collection.aggregate(pipeline))

    def recommend_recipes(self, user_preferences: Dict) -> List[Dict]:
        """
        Generate recipe recommendations based on user preferences
        
        Args:
            user_preferences (dict): User's dietary and taste preferences
        
        Returns:
            List of recommended recipes
        """
        recommendation_query = {
            "tags": {"$in": user_preferences.get('tags', [])},
            "difficulty": {"$lte": user_preferences.get('max_difficulty', 'Hard')}
        }
        
        recommended_recipes = list(
            self.recipes_collection.find(recommendation_query).limit(5)
        )
        
        return recommended_recipes

def main():
    print("Starting Recipe Manager Application")
    recipe_manager = RecipeManager()
    
    # Insert sample data
    print("Inserting sample data...")
    recipe_manager.insert_sample_recipes()
    
    # Demonstration of key features
    print("\nSearching Vegetarian Recipes:")
    vegetarian_recipes = recipe_manager.search_recipes({"tags": "vegetarian"})
    for recipe in vegetarian_recipes:
        print(f"- {recipe['name']} ({recipe['cuisine']} cuisine)")
    
    print("\nCuisine Aggregation:")
    cuisine_stats = recipe_manager.aggregate_recipes_by_cuisine()
    for cuisine in cuisine_stats:
        print(f"- {cuisine['_id']}: {cuisine['total_recipes']} recipes, " 
              f"Avg. Difficulty: {cuisine['average_difficulty']:.1f}")
    
    print("\nRecipe Recommendations:")
    user_prefs = {
        "tags": ["vegetarian", "quick-meal"],
        "max_difficulty": "Medium"
    }
    print(f"For user preferences: {user_prefs}")
    recommended = recipe_manager.recommend_recipes(user_prefs)
    for recipe in recommended:
        print(f"- {recipe['name']} ({recipe['difficulty']} difficulty)")
    
    print("\nRecipe Manager Demo Complete!")

if __name__ == "__main__":
    main()