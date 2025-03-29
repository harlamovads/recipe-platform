// MongoDB initialization script
// This script will be executed when the MongoDB container is created

// Create database
db = db.getSiblingDB('recipe_platform');

// Create collections with validation
db.createCollection('recipes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'ingredients', 'instructions', 'cuisine', 'difficulty'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        ingredients: {
          bsonType: 'array',
          description: 'must be an array and is required',
          items: {
            bsonType: 'object',
            required: ['name', 'quantity'],
            properties: {
              name: {
                bsonType: 'string',
                description: 'must be a string and is required'
              },
              quantity: {
                bsonType: 'string',
                description: 'must be a string and is required'
              }
            }
          }
        },
        instructions: {
          bsonType: 'array',
          description: 'must be an array of strings and is required',
          items: {
            bsonType: 'string'
          }
        },
        cuisine: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        difficulty: {
          bsonType: 'string',
          description: 'must be a string and is required',
          enum: ['Easy', 'Medium', 'Hard']
        }
      }
    }
  }
});

db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'email', 'password_hash'],
      properties: {
        username: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        email: {
          bsonType: 'string',
          description: 'must be a string and is required'
        },
        password_hash: {
          bsonType: 'string',
          description: 'must be a string and is required'
        }
      }
    }
  }
});

// Create indexes
db.recipes.createIndex({ "name": "text", "tags": "text", "cuisine": "text" });
db.recipes.createIndex({ "cuisine": 1 });
db.recipes.createIndex({ "difficulty": 1 });
db.recipes.createIndex({ "tags": 1 });
db.recipes.createIndex({ "user_id": 1 });
db.recipes.createIndex({ "created_at": 1 });

db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "favorite_recipes": 1 });

print('MongoDB initialization completed');