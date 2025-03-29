FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY recipe_manager.py .

# Add a healthcheck to verify the application is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import pymongo; pymongo.MongoClient('mongodb://mongodb:27017/').admin.command('ping')" || exit 1

CMD ["python", "recipe_manager.py"]