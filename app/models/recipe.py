from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Optional, Any, Union

class Recipe:
    """Recipe data model representing MongoDB document structure"""
    
    def __init__(self, 
                 name: str,
                 ingredients: List[Dict[str, str]],
                 instructions: List[str],
                 cuisine: str,
                 difficulty: str,
                 preparation_time: int,
                 cooking_time: int,
                 nutritional_info: Dict[str, Union[int, float]],
                 tags: List[str],
                 image_url: Optional[str] = None,
                 user_id: Optional[str] = None,
                 user_ratings: Optional[List[Dict[str, Any]]] = None,
                 comments: Optional[List[Dict[str, Any]]] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 _id: Optional[str] = None):
        """
        Initialize a Recipe object
        
        Args:
            name: Recipe name
            ingredients: List of ingredient objects with name and quantity
            instructions: List of step-by-step instructions
            cuisine: Type of cuisine
            difficulty: Difficulty level (Easy, Medium, Hard)
            preparation_time: Time in minutes for preparation
            cooking_time: Time in minutes for cooking
            nutritional_info: Nutritional information
            tags: List of tags for categorization
            image_url: URL to recipe image (optional)
            user_id: ID of the user who created the recipe (optional)
            user_ratings: List of user ratings (optional)
            comments: List of user comments (optional)
            created_at: Creation timestamp (optional)
            updated_at: Last update timestamp (optional)
            _id: MongoDB ObjectID (optional)
        """
        self.name = name
        self.ingredients = ingredients
        self.instructions = instructions
        self.cuisine = cuisine
        self.difficulty = difficulty
        self.preparation_time = preparation_time
        self.cooking_time = cooking_time
        self.nutritional_info = nutritional_info
        self.tags = tags
        self.image_url = image_url
        self.user_id = user_id
        self.user_ratings = user_ratings or []
        self.comments = comments or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._id = str(ObjectId()) if _id is None else _id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Recipe object to dictionary for MongoDB storage"""
        user_id_obj = ObjectId(self.user_id) if self.user_id and isinstance(self.user_id, str) else self.user_id
        
        return {
            "_id": ObjectId(self._id) if isinstance(self._id, str) else self._id,
            "name": self.name,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "cuisine": self.cuisine,
            "difficulty": self.difficulty,
            "preparation_time": self.preparation_time,
            "cooking_time": self.cooking_time,
            "nutritional_info": self.nutritional_info,
            "tags": self.tags,
            "image_url": self.image_url,
            "user_id": user_id_obj,
            "user_ratings": self.user_ratings,
            "comments": self.comments,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert Recipe object to dictionary for API responses with string IDs"""
        return {
            "_id": str(self._id),
            "name": self.name,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "cuisine": self.cuisine,
            "difficulty": self.difficulty,
            "preparation_time": self.preparation_time,
            "cooking_time": self.cooking_time,
            "nutritional_info": self.nutritional_info,
            "tags": self.tags,
            "image_url": self.image_url,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_ratings": self._convert_ids_to_str(self.user_ratings),
            "comments": self._convert_ids_to_str(self.comments),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def _convert_ids_to_str(items: List[Dict]) -> List[Dict]:
        """Convert ObjectId values to strings in a list of dictionaries"""
        if not items:
            return []
            
        result = []
        for item in items:
            item_copy = item.copy()
            # Convert any ObjectId to string
            for key, value in item_copy.items():
                if isinstance(value, ObjectId):
                    item_copy[key] = str(value)
                elif hasattr(value, 'isoformat'):  # Handle datetime objects
                    item_copy[key] = value.isoformat()
            result.append(item_copy)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipe':
        """Create Recipe object from MongoDB document"""
        if data is None:
            return None
            
        return cls(
            name=data.get('name'),
            ingredients=data.get('ingredients', []),
            instructions=data.get('instructions', []),
            cuisine=data.get('cuisine'),
            difficulty=data.get('difficulty'),
            preparation_time=data.get('preparation_time'),
            cooking_time=data.get('cooking_time'),
            nutritional_info=data.get('nutritional_info', {}),
            tags=data.get('tags', []),
            image_url=data.get('image_url'),
            user_id=str(data.get('user_id')) if data.get('user_id') else None,
            user_ratings=data.get('user_ratings', []),
            comments=data.get('comments', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=str(data.get('_id')) if data.get('_id') else None
        )

    @classmethod
    def create_indexes(cls, collection):
        """Create MongoDB indexes for recipe collection"""
        # Text index for search functionality
        collection.create_index([
            ("name", "text"),
            ("tags", "text"),
            ("cuisine", "text")
        ], name="recipe_search_index")
        
        # Other performance indexes
        collection.create_index("cuisine")
        collection.create_index("difficulty")
        collection.create_index("tags")
        collection.create_index("user_id")
        collection.create_index("created_at")