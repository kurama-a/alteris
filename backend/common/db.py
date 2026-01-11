from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase
import os

# ================================
#  Configuration MongoDB
# ================================
# Valeurs par défaut :
# - "localhost" pour un lancement en local
# - "mongo" pour Docker (service mongo dans docker-compose)
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "alternance_db")

# URI complète (surchargée par MONGO_URI si définie)
MONGO_URI = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:{MONGO_PORT}")

# ================================
#  Clients globaux
# ================================
client: AsyncIOMotorClient | None = None
db: AgnosticDatabase | None = None


async def connect_to_mongo():
    """
    Initialise la connexion MongoDB et stocke la base choisie dans `db`.
    """
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"✅ Connecté à MongoDB {MONGO_URI} (DB={MONGO_DB})")


async def close_mongo_connection():
    """
    Ferme proprement la connexion MongoDB.
    """
    global client
    if client:
        client.close()
        print("🛑 Connexion MongoDB fermée")