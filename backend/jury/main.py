import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.app_factory import create_app
from jury.routes import jury_api


#Lien pour accéder à l'api du micro service Jury
#http://localhost:8003/jury/docs
app = create_app(
    service_name="Jury",
    api=jury_api,
    prefix="/jury"
)