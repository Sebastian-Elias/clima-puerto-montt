import psycopg2

from src.config.settings import get_settings


def get_connection():
    settings = get_settings()

    try:
        return psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            sslmode=settings.db_sslmode,
        )
    except psycopg2.Error as error:
        raise ConnectionError(
            "No fue posible conectarse a la base de datos. "
            "Verifica que PostgreSQL esté ejecutándose y que la configuración sea correcta."
        ) from error