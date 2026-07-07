import logging

import psycopg2
from psycopg2.extras import execute_values

from config.settings import get_settings

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather_daily (
    city TEXT NOT NULL,
    date DATE NOT NULL,
    temperature_2m_max REAL,
    temperature_2m_min REAL,
    temperature_2m_mean REAL,
    PRIMARY KEY (city, date)
);
"""

UPSERT_SQL = """
INSERT INTO weather_daily (city, date, temperature_2m_max, temperature_2m_min, temperature_2m_mean)
VALUES %s
ON CONFLICT (city, date) DO UPDATE SET
    temperature_2m_max = EXCLUDED.temperature_2m_max,
    temperature_2m_min = EXCLUDED.temperature_2m_min,
    temperature_2m_mean = EXCLUDED.temperature_2m_mean;
"""


def get_connection():
    settings = get_settings()
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        sslmode=settings.db_sslmode,
    )


def load_weather(registros):
    if not registros:
        logger.info("No hay registros para cargar")
        return 0

    valores = [
        (
            registro["city"],
            registro["date"],
            registro["temperature_2m_max"],
            registro["temperature_2m_min"],
            registro["temperature_2m_mean"],
        )
        for registro in registros
    ]

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL)
                execute_values(cursor, UPSERT_SQL, valores)

        logger.info(f"Carga finalizada. Total de registros insertados/actualizados: {len(valores)}")
        return len(valores)
    finally:
        conn.close()
