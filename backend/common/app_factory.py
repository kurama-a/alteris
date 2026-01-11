from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.db import connect_to_mongo, close_mongo_connection

def create_app(service_name: str, api, prefix: str) -> FastAPI:
    app = FastAPI(
        title=f"API {service_name}",
        description=f"Documentation de l’API {service_name}",
        version="1.0.0",
        openapi_url=f"{prefix}/openapi.json",  # Ex: /apprenti/openapi.json
        docs_url=f"{prefix}/docs",            # Ex: /apprenti/docs
        redoc_url=f"{prefix}/redoc"           # Ex: /apprenti/redoc
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.on_event("startup")
    async def startup_db():
        await connect_to_mongo()

    @app.on_event("shutdown")
    async def shutdown_db():
        await close_mongo_connection()

    app.include_router(api, prefix=prefix)

    @app.get(f"{prefix}/health", tags=["System"])
    def health():
        return {"status": "ok", "service": service_name.lower()}

    return app
