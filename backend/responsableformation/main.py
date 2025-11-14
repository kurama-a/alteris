import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from responsableformation.routes import responsableformation_api

# Lien pour accéder à l'API du microservice Responsable Formation
# http://localhost:XXXX/responsableformation/docs
app = create_app(
    service_name="ResponsableFormation",
    api=responsableformation_api,
    prefix="/responsableformation"
)