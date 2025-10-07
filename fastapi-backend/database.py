from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

MONGODB_URI = "mongodb+srv://avinash:949367%40Sv@park-pro.rxeddmo.mongodb.net/?retryWrites=true&w=majority&appName=park-pro"

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    try:
        mongodb.client = AsyncIOMotorClient(MONGODB_URI)
        # Use a specific database name, e.g., "park_pro"
        mongodb.db = mongodb.client["test"]
        # Test connection
        await mongodb.client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")

async def close_mongo_connection():
    mongodb.client.close()
