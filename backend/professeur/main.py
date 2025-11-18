import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from professeur.routes import professeur_api


#Lien pour accéder à l'api du micro service Professeur
#http://localhost:8003/professeur/docs
app = create_app(
    service_name="Professeur",
    api=professeur_api,
    prefix="/professeur"
)