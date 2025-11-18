import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from routes import entreprise_api

app = create_app(
    service_name="Entreprise",
    api=entreprise_api,
    prefix="/entreprise"
)
