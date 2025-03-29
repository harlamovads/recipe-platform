from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Optional, Any, Set
import hashlib

class User:
    """User data model representing MongoDB document structure"""
    
    def __init__(self,
                 username: str,
                 email: str,
                 password_hash: str,
                 dietary_preferences: Optional[List[str]] = None,
                 favorite_cuisines: Optional[List[str]] = None,
                 favorite_recipes: Optional[List[str]] = None,
                 cooking_skill_level: str = "Beginner",
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 _id: Optional[str] = None):
        """
        Initialize a User object
        
        Args:
            username: Unique username
            email: User's email address
            password_hash: Hashed password
            dietary_preferences: List of dietary preferences (e.g., vegetarian, vegan)
            favorite_cuisines: List of favorite cuisine types
            favorite_recipes: List of favorite recipe IDs
            cooking_skill_level: User's cooking skill level
            created_at: Creation timestamp
            updated_at: Last update timestamp
            _id: MongoDB ObjectID
        """
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.dietary_preferences = dietary_preferences or []
        self.favorite_cuisines = favorite_cuisines or []
        self.favorite_recipes = favorite_recipes or []
        self.cooking_skill_level = cooking_skill_level
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._id = str(ObjectId()) if _id is None else _id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User object to dictionary for MongoDB storage"""
        favorite_recipes_as_objids = [
            ObjectId(recipe_id) if isinstance(recipe_id, str) else recipe_id
            for recipe_id in self.favorite_recipes
        ]
        
        return {
            "_id": ObjectId(self._id) if isinstance(self._id, str) else self._id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "dietary_preferences": self.dietary_preferences,
            "favorite_cuisines": self.favorite_cuisines,
            "favorite_recipes": favorite_recipes_as_objids,
            "cooking_skill_level": self.cooking_skill_level,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User object from MongoDB document"""
        if data is None:
            return None
        favorite_recipes = []
        if data.get("favorite_recipes"):
            favorite_recipes = [str(recipe_id) for recipe_id in data["favorite_recipes"]]
            
        return cls(
            username=data.get("username"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            dietary_preferences=data.get("dietary_preferences", []),
            favorite_cuisines=data.get("favorite_cuisines", []),
            favorite_recipes=favorite_recipes,
            cooking_skill_level=data.get("cooking_skill_level", "Beginner"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            _id=str(data.get("_id")) if data.get("_id") else None
        )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the stored hash"""
        password_hash = self.hash_password(password)
        return self.password_hash == password_hash
    
    def add_favorite_recipe(self, recipe_id: str) -> None:
        """Add a recipe to favorites"""
        if recipe_id not in self.favorite_recipes:
            self.favorite_recipes.append(recipe_id)
            
    def remove_favorite_recipe(self, recipe_id: str) -> None:
        """Remove a recipe from favorites"""
        if recipe_id in self.favorite_recipes:
            self.favorite_recipes.remove(recipe_id)
    
    @classmethod
    def create_indexes(cls, collection):
        """Create MongoDB indexes for user collection"""
        collection.create_index("username", unique=True)
        collection.create_index("email", unique=True)
        collection.create_index("favorite_recipes")
        collection.create_index("dietary_preferences")
        collection.create_index("favorite_cuisines")
        
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert User object to dictionary for API responses with string IDs"""
        return {
            "_id": str(self._id),
            "username": self.username,
            "email": self.email,
            "dietary_preferences": self.dietary_preferences,
            "favorite_cuisines": self.favorite_cuisines,
            "favorite_recipes": [str(recipe_id) for recipe_id in self.favorite_recipes] if self.favorite_recipes else [],
            "cooking_skill_level": self.cooking_skill_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }