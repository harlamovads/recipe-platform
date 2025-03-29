# Recipe Discovery Platform

A full-featured recipe management and discovery platform built with Flask and MongoDB, showcasing the power of NoSQL document-oriented databases for flexible content management.

## Project Overview

The Recipe Discovery Platform is a comprehensive web application that enables users to:

- Browse, search, and filter recipes by various criteria
- Create and manage their own recipes
- Save favorite recipes for quick access
- Receive personalized recipe recommendations
- Interact with recipes through comments
- View recipe statistics and analytics

This project demonstrates how MongoDB's document-oriented structure and flexible schema are ideal for content management systems where data has varying attributes and relationships.

## Key MongoDB Features Demonstrated

1. **Document-Oriented Storage**
   - Complex nested data structures for recipes (ingredients, instructions, nutritional info)
   - Embedded arrays for comments, ratings, and ingredients
   - Flexible schema allowing varying recipe attributes

2. **Advanced Querying**
   - Full-text search across recipe content
   - Multi-criteria filtering (cuisine, difficulty, cooking time)
   - Complex logical combinations of query parameters

3. **Aggregation Framework**
   - Recipe statistics by cuisine, difficulty, etc.
   - Comment counts per user
   - Average cooking and preparation times
   - Popular tags analysis

4. **Indexing Strategies**
   - Text indexes for search functionality
   - Single-field indexes for sorting and filtering
   - Compound indexes for query optimization

5. **Data Relationships**
   - User-to-recipe references (favorites, authored recipes)
   - Embedded comments within recipes
   - Cross-collection data lookups

## Technology Stack

- **Backend**: Python 3.9, Flask
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Containerization**: Docker, Docker Compose

## Project Structure

```
recipe-platform/
├── app/
│   ├── models/              # Data models
│   │   ├── recipe.py        # Recipe model definition
│   │   └── user.py          # User model definition
│   ├── services/            # Business logic
│   │   ├── recipe_service.py # Recipe-related operations
│   │   └── user_service.py  # User-related operations
│   ├── static/              # Static assets
│   │   ├── css/             # CSS files
│   │   ├── js/              # JavaScript files 
│   │   └── img/             # Image assets
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html        # Base template
│   │   ├── index.html       # Homepage
│   │   ├── stats.html       # Statistics page
│   │   ├── recipes/         # Recipe-related templates
│   │   └── users/           # User-related templates
│   ├── views/               # Route handlers
│   │   ├── main.py          # Main routes
│   │   ├── recipe.py        # Recipe routes
│   │   └── user.py          # User routes
│   ├── __init__.py          # Application factory
│   └── config.py            # Configuration settings
├── docker/                  # Docker configuration
│   ├── app/                 # App container configuration
│   └── mongo/               # MongoDB container configuration
├── scripts/                 # Utility scripts
│   └── seed_data.py         # Database seeding
├── .env.example             # Environment variables template
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
└── run.py                   # Application entry point
```

## Key Features

### Recipe Management
- Create, read, update, and delete recipes
- Rich recipe details including ingredients, instructions, nutritional info
- Image support for recipes
- Interactive comments system

### User Experience
- User registration and authentication
- Personalized recipe recommendations based on preferences
- Favorite recipes collection
- User profiles with activity statistics

### Search and Discovery
- Full-text search across recipe content
- Multi-criteria filtering (cuisine, difficulty, cooking time)
- Tag-based navigation
- Sorting options for recipe lists

### Analytics and Visualization
- Recipe statistics dashboard
- Cuisine distribution
- Difficulty breakdown
- Cooking time analysis
- Tag popularity metrics

## Running the Application

### Prerequisites
- Docker and Docker Compose
- Git (optional)

### Setup and Installation

1. Clone the repository (or download the code):
   ```bash
   git clone https://github.com/zlovoblachko/recipe-platform.git
   cd recipe-platform
   ```

2. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

3. Start the application with Docker Compose:
   ```bash
   docker compose up -d
   ```

4. Seed the database with sample data:
   ```bash
   docker compose exec app python scripts/seed_data.py
   ```

5. Access the application at:
   ```
   http://localhost:5000
   ```

### Sample User Accounts

The seed script creates the following user accounts for testing:

- Username: `chef_john`, Password: `password123`
- Username: `foodie_sara`, Password: `password123`
- Username: `beginner_cook`, Password: `password123`

## MongoDB Schema Design

### Recipes Collection

```javascript
{
  "_id": ObjectId,
  "name": "String",
  "ingredients": [
    {"name": "String", "quantity": "String"}
  ],
  "instructions": ["String"],
  "cuisine": "String",
  "difficulty": "String", // "Easy", "Medium", "Hard"
  "preparation_time": Number,
  "cooking_time": Number,
  "nutritional_info": {
    "calories": Number,
    "protein": Number,
    "carbs": Number,
    "fat": Number
  },
  "tags": ["String"],
  "image_url": "String",
  "user_id": ObjectId, // Reference to the creator
  "user_ratings": [
    {"user_id": ObjectId, "rating": Number, "date": Date}
  ],
  "comments": [
    {
      "user_id": ObjectId,
      "username": "String",
      "text": "String",
      "date": Date
    }
  ],
  "created_at": Date,
  "updated_at": Date
}
```

### Users Collection

```javascript
{
  "_id": ObjectId,
  "username": "String",
  "email": "String",
  "password_hash": "String",
  "dietary_preferences": ["String"],
  "favorite_cuisines": ["String"],
  "favorite_recipes": [ObjectId], // References to Recipe documents
  "cooking_skill_level": "String", // "Beginner", "Intermediate", "Advanced"
  "created_at": Date,
  "updated_at": Date
}
```

## MongoDB Query Examples

### Full-Text Search

```javascript
db.recipes.find(
  { "$text": { "$search": "vegetarian pasta" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
```

### Multi-Criteria Filtering

```javascript
db.recipes.find({
  "cuisine": "Italian",
  "difficulty": { "$in": ["Easy", "Medium"] },
  "cooking_time": { "$lte": 30 },
  "tags": { "$in": ["vegetarian"] }
})
```

### Aggregation for Statistics

```javascript
db.recipes.aggregate([
  { "$unwind": "$tags" },
  { "$group": {
      "_id": "$tags",
      "count": { "$sum": 1 }
  }},
  { "$sort": { "count": -1 } },
  { "$limit": 10 }
])
```

### User's Comment Count

```javascript
db.recipes.aggregate([
  { "$match": { "comments.user_id": ObjectId("user_id_here") } },
  { "$unwind": "$comments" },
  { "$match": { "comments.user_id": ObjectId("user_id_here") } },
  { "$count": "total_comments" }
])
```