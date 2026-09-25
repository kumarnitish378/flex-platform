"""Imports every model module so `Base.metadata` is complete.

Alembic autogenerate compares the database against `Base.metadata`; a model module that
nobody imports is invisible to it and silently never gets a migration. Import new model
modules here, and nowhere else, so there is one place to check.
"""

from app.modules.alerts import models as alert_models
from app.modules.auth import models as auth_models
from app.modules.config import models as config_models
from app.modules.fleet import duty_models as fleet_duty_models
from app.modules.fleet import models as fleet_models
from app.modules.people import models as people_models
from app.modules.requests import models as request_models
from app.modules.tenancy import models as tenancy_models
from app.modules.tracking import models as tracking_models

__all__ = [
    "alert_models",
    "auth_models",
    "config_models",
    "fleet_duty_models",
    "fleet_models",
    "people_models",
    "request_models",
    "tenancy_models",
    "tracking_models",
]
