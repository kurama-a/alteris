import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from common.db import connect_to_mongo, close_mongo_connection
from auth.routes import auth_api

app = create_app(
    service_name="Auth",
    api=auth_api,
    prefix="/auth"
)

# === Connexion MongoDB ===
@app.on_event("startup")
async def startup_db():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db():
    await close_mongo_connection()