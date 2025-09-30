from common.app_factory import create_app
from maitre.routes import maitre_api
# Lien d'accès à l'api 
#http://localhost:8002/maitre/docs

app = create_app(
    service_name="Maitre",
    api=maitre_api,
    prefix="/maitre"
)