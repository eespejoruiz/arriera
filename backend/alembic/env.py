from sqlalchemy import engine_from_config, pool

import arriera.models  # noqa: F401  (registra los modelos)
from alembic import context
from arriera.config import settings
from arriera.db import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings().database_url)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    conectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with conectable.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
