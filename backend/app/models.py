"""Imports every model module so `Base.metadata` is complete.

Alembic autogenerate compares the database against `Base.metadata`; a model module that
nobody imports is invisible to it and silently never gets a migration. Import new model
modules here, and nowhere else, so there is one place to check.
"""

from app.modules.auth import models as auth_models
from app.modules.people import models as people_models
from app.modules.tenancy import models as tenancy_models

__all__ = ["auth_models", "people_models", "tenancy_models"]
