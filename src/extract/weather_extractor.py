import logging

import requests

from config.settings import get_settings

logger = logging.getLogger(__name__)

CIUDADES = {
    "Puerto Montt": {"lat": -41.47, "lon": -72.94},
}


def extract_weather():
    settings = get_settings()
    weather_data = []

    for ciudad, coordenadas in CIUDADES.items():
        params = {
            "latitude": coordenadas["lat"],
            "longitude": coordenadas["lon"],
            "start_date": settings.weather_start_date,
            "end_date": settings.weather_end_date,
            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "temperature_2m_mean"
            ),
            "timezone": "America/Santiago",
        }

        try:
            logger.info(f"Inicia extracción de datos para {ciudad}")

            response = requests.get(settings.api_url, params=params)
            response.raise_for_status()

            logger.info(f"Datos obtenidos correctamente para {ciudad}")

            data = response.json()
            data["city"] = ciudad

            weather_data.append(data)

        except requests.RequestException as error:
            logger.error(f"No fue posible obtener datos para {ciudad}: {error}")

    return weather_data