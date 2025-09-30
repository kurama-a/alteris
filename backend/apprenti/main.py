from common.app_factory import create_app
from apprenti.routes import apprenti_api  # ← changement ici

app = create_app(
    service_name="Apprenti",
    api=apprenti_api,
    prefix="/apprenti"
)