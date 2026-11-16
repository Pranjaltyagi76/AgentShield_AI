from alembic import context

from app.core.settings import Settings
from app.db import runs  # noqa: F401  (register run tables)
from app.db.connection import Database
from app.db.models import Base

database = Database(Settings())
if database.engine is None:
    raise RuntimeError("DATABASE_URL required for migrations")
try:
    with database.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
finally:
    database.close()
