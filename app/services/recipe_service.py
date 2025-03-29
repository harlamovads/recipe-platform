from typing import Dict, List, Optional, Union, Any
from bson import ObjectId
from datetime import datetime
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from app import mongo
from app.models.recipe import Recipe
from app.config import Config

class RecipeService:
    """Service class for recipe-related operations"""
    
    @property
    def collection(self) -> Collection:
        """Get MongoDB collection for recipes"""
        return mongo.db[Config.RECIPES_COLLECTION]
    
    def create_recipe(self, recipe_data: Dict[str, Any]) -> str:
        """
        Create a new recipe
        
        Args:
            recipe_data: Recipe data dictionary
            
        Returns:
            str: ID of the created recipe
        """
        recipe = Recipe(**recipe_data)
        result: InsertOneResult = self.collection.insert_one(recipe.to_dict())
        return str(result.inserted_id)
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Recipe]:
        """
        Get recipe by ID
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            Recipe object or None if not found
        """
        try:
            recipe_data = self.collection.find_one({"_id": ObjectId(recipe_id)})
            return Recipe.from_dict(recipe_data) if recipe_data else None
        except Exception:
            return None
    
    def update_recipe(self, recipe_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update recipe
        
        Args:
            recipe_id: Recipe ID
            update_data: Fields to update
            
        Returns:
            bool: True if update was successful
        """
        update_data["updated_at"] = datetime.utcnow()
        
        result: UpdateResult = self.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    def delete_recipe(self, recipe_id: str) -> bool:
        """
        Delete recipe
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            bool: True if deletion was successful
        """
        result: DeleteResult = self.collection.delete_one({"_id": ObjectId(recipe_id)})
        return result.deleted_count > 0
    
    def search_recipes(self, 
                      query: Optional[str] = None, 
                      filters: Optional[Dict[str, Any]] = None,
                      page: int = 1, 
                      page_size: int = 10) -> Dict[str, Any]:
        """
        Search recipes with pagination
        
        Args:
            query: Text search query
            filters: Additional filters
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dict containing recipes and pagination metadata
        """
        # Build the query
        search_query = {}
        
        # Text search if query provided
        if query:
            search_query["$text"] = {"$search": query}
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if key == 'tags' and isinstance(value, list):
                    search_query["tags"] = {"$in": value}
                elif key == 'difficulty' and isinstance(value, list):
                    search_query["difficulty"] = {"$in": value}
                elif key == 'preparation_time_max' and isinstance(value, int):
                    search_query["preparation_time"] = {"$lte": value}
                elif key == 'cooking_time' and isinstance(value, dict) and "$lte" in value:
                    search_query["cooking_time"] = value
                elif key == 'cooking_time_max' and isinstance(value, int):
                    search_query["cooking_time"] = {"$lte": value}
                else:
                    search_query[key] = value
        
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Execute query with pagination
        count = self.collection.count_documents(search_query)
        cursor = self.collection.find(search_query).skip(skip).limit(page_size)
        
        # Convert to Recipe objects
        recipes = [Recipe.from_dict(doc) for doc in cursor]
        
        # Build pagination metadata
        total_pages = (count + page_size - 1) // page_size
        
        return {
            "recipes": recipes,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": count,
                "total_pages": total_pages
            }
        }
    
    def get_recipes_by_user(self, user_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get recipes created by a specific user
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page
            
        Returns:
            Dict containing recipes and pagination metadata
        """
        return self.search_recipes(filters={"user_id": ObjectId(user_id)}, page=page, page_size=page_size)
    
    def get_popular_recipes(self, limit: int = 10) -> List[Recipe]:
        """
        Get most popular recipes based on ratings
        
        Args:
            limit: Maximum number of recipes to return
            
        Returns:
            List of Recipe objects
        """
        pipeline = [
            {"$match": {"user_ratings": {"$exists": True, "$ne": []}}},
            {"$addFields": {
                "average_rating": {"$avg": "$user_ratings.rating"},
                "ratings_count": {"$size": "$user_ratings"}
            }},
            {"$sort": {"average_rating": -1, "ratings_count": -1}},
            {"$limit": limit}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return [Recipe.from_dict(doc) for doc in result]
    
    def get_user_recipes(self, user_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get recipes created by a specific user
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page
            
        Returns:
            Dict containing recipes and pagination metadata
        """
        # Convert user_id to ObjectId
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Build query for user's recipes
        query = {"user_id": user_id_obj}
        
        # Calculate pagination
        skip = (page - 1) * page_size
        
        # Execute query with pagination
        count = self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
        
        # Convert to Recipe objects
        recipes = [Recipe.from_dict(doc) for doc in cursor]
        
        # Build pagination metadata
        total_pages = (count + page_size - 1) // page_size if count > 0 else 1
        
        return {
            "recipes": recipes,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": count,
                "total_pages": total_pages
            }
        }
    
    def count_user_comments(self, user_id: str) -> int:
        """
        Count the number of comments made by a user across all recipes
        
        Args:
            user_id: User ID
            
        Returns:
            Number of comments made by the user
        """
        pipeline = [
            # Find recipes containing comments by this user
            {"$match": {"comments.user_id": user_id}},
            # Unwind to get individual comments
            {"$unwind": "$comments"},
            # Filter to just the user's comments
            {"$match": {"comments.user_id": user_id}},
            # Count the comments
            {"$count": "total_comments"}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result[0].get("total_comments", 0) if result else 0
    
    def get_recipe_stats(self) -> Dict[str, Any]:
        """
        Get recipe statistics
        
        Returns:
            Dict containing various recipe statistics
        """
        # Count by cuisine
        cuisine_pipeline = [
            {"$group": {"_id": "$cuisine", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        cuisine_stats = list(self.collection.aggregate(cuisine_pipeline))
        
        # Count by difficulty
        difficulty_pipeline = [
            {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        difficulty_stats = list(self.collection.aggregate(difficulty_pipeline))
        
        # Average preparation and cooking time
        time_pipeline = [
            {"$group": {
                "_id": None,
                "avg_prep_time": {"$avg": "$preparation_time"},
                "avg_cook_time": {"$avg": "$cooking_time"}
            }}
        ]
        time_stats = list(self.collection.aggregate(time_pipeline))
        
        # Most common tags
        tag_pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        tag_stats = list(self.collection.aggregate(tag_pipeline))
        
        return {
            "total_recipes": self.collection.count_documents({}),
            "cuisines": cuisine_stats,
            "difficulties": difficulty_stats,
            "time_stats": time_stats[0] if time_stats else {},
            "popular_tags": tag_stats
        }
        
    def add_comment(self, recipe_id: str, comment_data: Dict[str, Any]) -> bool:
        """
        Add a comment to a recipe
        
        Args:
            recipe_id: Recipe ID
            comment_data: Comment data including user_id, username, text, and date
            
        Returns:
            bool: True if comment was added successfully
        """
        # Ensure the comment has a timestamp
        if 'date' not in comment_data:
            comment_data['date'] = datetime.utcnow()
            
        result = self.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$push": {"comments": comment_data}}
        )
        
        return result.modified_count > 0
    
    def get_similar_recipes(self, recipe_id: str, limit: int = 3) -> List[Recipe]:
        """
        Get similar recipes based on tags and cuisine
        
        Args:
            recipe_id: Recipe ID to find similar recipes for
            limit: Maximum number of similar recipes to return
            
        Returns:
            List of similar Recipe objects
        """
        # Get the source recipe
        source_recipe = self.get_recipe_by_id(recipe_id)
        if not source_recipe:
            return []
            
        # Build a query to find similar recipes
        query = {
            "_id": {"$ne": ObjectId(recipe_id)},  # Exclude the source recipe
            "$or": [
                {"tags": {"$in": source_recipe.tags}},  # Similar tags
                {"cuisine": source_recipe.cuisine}      # Same cuisine
            ]
        }
        
        # Find similar recipes and sort by relevance
        # The more tags in common, the higher the score
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "commonTags": {
                    "$size": {
                        "$setIntersection": ["$tags", source_recipe.tags]
                    }
                },
                "sameCuisine": {
                    "$cond": [{"$eq": ["$cuisine", source_recipe.cuisine]}, 1, 0]
                }
            }},
            {"$addFields": {
                "relevanceScore": {"$add": ["$commonTags", "$sameCuisine"]}
            }},
            {"$sort": {"relevanceScore": -1}},
            {"$limit": limit}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return [Recipe.from_dict(doc) for doc in result]