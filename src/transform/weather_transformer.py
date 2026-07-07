import logging

logger = logging.getLogger(__name__)


def transform_weather(weather_data):
    registros = []

    for ciudad_data in weather_data:
        ciudad = ciudad_data["city"]
        logger.info(f"Procesando ciudad: {ciudad}")

        daily = ciudad_data["daily"]

        for (
            fecha,
            temp_max,
            temp_min,
            temp_media,
        ) in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["temperature_2m_mean"],
        ):

            registro = {
                "city": ciudad,
                "date": fecha,
                "temperature_2m_max": temp_max,
                "temperature_2m_min": temp_min,
                "temperature_2m_mean": temp_media,
            }

            registros.append(registro)

    logger.info(f"Transformación finalizada. Total de registros: {len(registros)}")

    return registros