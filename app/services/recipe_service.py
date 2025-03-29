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
        recipe = Recipe(**recipe_data)
        result: InsertOneResult = self.collection.insert_one(recipe.to_dict())
        return str(result.inserted_id)
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Recipe]:
        try:
            recipe_data = self.collection.find_one({"_id": ObjectId(recipe_id)})
            return Recipe.from_dict(recipe_data) if recipe_data else None
        except Exception:
            return None
    
    def update_recipe(self, recipe_id: str, update_data: Dict[str, Any]) -> bool:
        update_data["updated_at"] = datetime.utcnow()
        
        result: UpdateResult = self.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    def delete_recipe(self, recipe_id: str) -> bool:
        result: DeleteResult = self.collection.delete_one({"_id": ObjectId(recipe_id)})
        return result.deleted_count > 0
    
    def search_recipes(self, 
                      query: Optional[str] = None, 
                      filters: Optional[Dict[str, Any]] = None,
                      page: int = 1, 
                      page_size: int = 10) -> Dict[str, Any]:
        search_query = {}
        if query:
            search_query["$text"] = {"$search": query}
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
        skip = (page - 1) * page_size
        count = self.collection.count_documents(search_query)
        cursor = self.collection.find(search_query).skip(skip).limit(page_size)
        recipes = [Recipe.from_dict(doc) for doc in cursor]
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
        return self.search_recipes(filters={"user_id": ObjectId(user_id)}, page=page, page_size=page_size)

    def get_popular_recipes(self, limit: int = 10) -> List[Recipe]:
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
        user_id_obj = ObjectId(user_id) if isinstance(user_id, str) else user_id
        query = {"user_id": user_id_obj}
        skip = (page - 1) * page_size
        count = self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
        recipes = [Recipe.from_dict(doc) for doc in cursor]
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
        pipeline = [
            {"$match": {"comments.user_id": user_id}},
            {"$unwind": "$comments"},
            {"$match": {"comments.user_id": user_id}},
            {"$count": "total_comments"}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0].get("total_comments", 0) if result else 0
    
    def get_recipe_stats(self) -> Dict[str, Any]:
        cuisine_pipeline = [
            {"$group": {"_id": "$cuisine", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        cuisine_stats = list(self.collection.aggregate(cuisine_pipeline))
        difficulty_pipeline = [
            {"$group": {"_id": "$difficulty", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        difficulty_stats = list(self.collection.aggregate(difficulty_pipeline))
        time_pipeline = [
            {"$group": {
                "_id": None,
                "avg_prep_time": {"$avg": "$preparation_time"},
                "avg_cook_time": {"$avg": "$cooking_time"}
            }}
        ]
        time_stats = list(self.collection.aggregate(time_pipeline))
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
        if 'date' not in comment_data:
            comment_data['date'] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(recipe_id)},
            {"$push": {"comments": comment_data}}
        )
        return result.modified_count > 0
    
    def get_similar_recipes(self, recipe_id: str, limit: int = 3) -> List[Recipe]:
        source_recipe = self.get_recipe_by_id(recipe_id)
        if not source_recipe:
            return []
        query = {
            "_id": {"$ne": ObjectId(recipe_id)}, 
            "$or": [
                {"tags": {"$in": source_recipe.tags}},
                {"cuisine": source_recipe.cuisine}
            ]
        }
        # find similar recipes and sort by relevance
        # The more tags in common, the better
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