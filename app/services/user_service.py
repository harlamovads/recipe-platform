from typing import Dict, List, Optional, Union, Any
from bson import ObjectId
from datetime import datetime
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from app import mongo
from app.models.user import User
from app.config import Config

class UserService:
    @property
    def collection(self) -> Collection:
        return mongo.db[Config.USERS_COLLECTION]
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        if 'password' in user_data:
            user_data['password_hash'] = User.hash_password(user_data.pop('password'))
        user = User(**user_data)
        try:
            result = self.collection.insert_one(user.to_dict())
            return {"user_id": str(result.inserted_id), "status": "success"}
        except DuplicateKeyError:
            return {"status": "error", "message": "Username or email already exists"}
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_data = self.collection.find_one({"_id": ObjectId(user_id)})
            return User.from_dict(user_data) if user_data else None
        except Exception:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        user_data = self.collection.find_one({"username": username})
        return User.from_dict(user_data) if user_data else None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        user_data = self.collection.find_one({"email": email})
        return User.from_dict(user_data) if user_data else None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if user and user.verify_password(password):
            return user
        return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        if 'password' in update_data:
            update_data['password_hash'] = User.hash_password(update_data.pop('password'))
        update_data["updated_at"] = datetime.utcnow()
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False
    
    def add_favorite_recipe(self, user_id: str, recipe_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"favorite_recipes": ObjectId(recipe_id)}}
        )
        return result.modified_count > 0
    
    def remove_favorite_recipe(self, user_id: str, recipe_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"favorite_recipes": ObjectId(recipe_id)}}
        )
        return result.modified_count > 0
    
    def get_favorite_recipes(self, user_id: str) -> List[str]:
        user = self.get_user_by_id(user_id)
        return user.favorite_recipes if user else []
    
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        update_data = {}
        if 'dietary_preferences' in preferences:
            update_data['dietary_preferences'] = preferences['dietary_preferences']
        if 'favorite_cuisines' in preferences:
            update_data['favorite_cuisines'] = preferences['favorite_cuisines']
        if 'cooking_skill_level' in preferences:
            update_data['cooking_skill_level'] = preferences['cooking_skill_level']
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        return False
    
    def get_recommendation_profile(self, user_id: str) -> Dict[str, Any]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        return {
            "dietary_preferences": user.dietary_preferences,
            "favorite_cuisines": user.favorite_cuisines,
            "cooking_skill_level": user.cooking_skill_level,
            "favorite_recipes": user.favorite_recipes
        }