# -*- encoding: utf-8 -*-
import logging

from rhasspy_weather.data_types.report import WeatherReport
import rhasspy_weather.data_types.config as cf
from rhasspy_weather.data_types.error import WeatherError
from rhasspy_weather.templates import fill_template

log = logging.getLogger(__name__)

# TODO: find a better name for this file


# function being called when rhasspy detects an intent related to the weather
def get_weather_forecast(intent_message, config_path=None):
    if config_path is not None:
        cf.set_config_path(config_path)

    config = cf.get_config()

    try:
        log.info("Parsing rhasspy intent")
        request = config.parser.parse_intent_message(intent_message)

        log.info("Requesting weather")
        forecast = config.api.get_weather(request.location)

        log.info("Formulating answer")
        output = WeatherReport(request, forecast)
    except WeatherError as error:
        output = error

    log.info("Answering")
    for output_item in config.output:
        try:
            filled_template = fill_template(intent_message, output, output_item.get_template())
            output_item.output_response(filled_template)
        except WeatherError as e:
            log.error(f"Can't output response on {output_item.__name__}: {e.description}")

    return output
