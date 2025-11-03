import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from coordonatrice.routes import coordonatrice_api

#Lien pour accéder à l'API du microservice Coordinatrice
# http://localhost:8004/coordonatrice/docs
app = create_app(
    service_name="Coordonatrice",
    api=coordonatrice_api,
    prefix="/coordonatrice"
)