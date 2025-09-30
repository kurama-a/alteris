import os

class Settings:
    # Port injecté par l'env de chaque API
    APP_PORT = int(os.getenv("APP_PORT", 8000))

    # Une seule base MongoDB pour tout le monde
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    MONGO_DB = os.getenv("MONGO_DB", "alternance_db")

settings = Settings()