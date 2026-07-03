from pymongo import MongoClient
from django.conf import settings

client = MongoClient(settings.MONGO_URI)

db = client[settings.DATABASE_NAME]

users_collection = db["users"]

booking_collection = db["bookings"]

vehicle_collection = db["vehicles"]

driver_collection = db["drivers"]

fuel_collection = db["fuel"]

maintenance_collection = db["maintenance"]

payment_collection = db["payments"]