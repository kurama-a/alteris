from common.app_factory import create_app
from tuteur.routes import tuteur_api


#Lien pour accéder à l'api du micro service Tuteur
#http://localhost:8003/tuteur/docs

app = create_app(
    service_name="Tuteur",
    api=tuteur_api,
    prefix="/tuteur"
)