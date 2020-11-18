# -*- encoding: utf-8 -*-
import logging

from rhasspy_weather.data_types.forecast import WeatherForecast
from rhasspy_weather.data_types.report import WeatherReport
import rhasspy_weather.data_types.config as cf
from rhasspy_weather.data_types.error import WeatherError, ConfigError
from rhasspy_weather.data_types.request import WeatherRequest
from rhasspy_weather.templates import fill_template

log = logging.getLogger(__name__)


# TODO: find a better name for this file


def get_weather_forecast(weather_input, config_path: str = None):
    """
    Function that takes any valid input format (see parser for what is supported) and answers.

    Args:
        weather_input: anything that a parser exists for
        config_path: optional path to a config file

    Returns:
        output, unless one of the selected outputs has a specified return value. If there is one, it will return that instead

    """
    try:
        request = get_request(weather_input, config_path)
        forecast = get_weather(request, config_path)
        output = get_report(request, forecast)
    except WeatherError as error:
        output = error

    answer_value = answer(weather_input, output, config_path)

    return answer_value


def get_request(weather_input, config_path: str = None) -> WeatherRequest:
    """
    Function that takes any valid input (see parsers for what can be used here) and returns a WeatherRequest
    Args:
        weather_input: anything that a parser exists for
        config_path: optional path to a config file

    Returns:
        WeatherRequest containing the information from weather_input

    """
    if config_path is not None and cf.config_path is not config_path:
        cf.set_config_path(config_path)

    config = cf.get_config()
    log.info("Parsing rhasspy intent")
    request = config.parser.parse_intent_message(weather_input)

    return request


def get_weather(request: WeatherRequest, config_path: str = None) -> WeatherForecast:
    """
    Function taking a WeatherRequest and returning the weather forecast for the time around the request

    Args:
        request: WeatherRequest object
        config_path: optional path to a config file

    Returns:
        WeatherForecast object

    """
    if config_path is not None and cf.config_path is not config_path:
        cf.set_config_path(config_path)

    config = cf.get_config()
    log.info("Requesting weather")
    forecast = config.api.get_weather(request.location)

    return forecast


def get_report(request: WeatherRequest, forecast: WeatherForecast, config_path: str = None) -> WeatherReport:
    """
    Function that takes a WeatherRequest and a WeatherForecast and turns those into a finished WeatherReport

    Args:
        request: WeatherRequest object
        forecast: WeatherForecast object
        config_path: optional path to a config file

    Returns:
        WeatherReport object containing the answer to the request as well as all the relevant weather information

    """
    if config_path is not None and cf.config_path is not config_path:
        cf.set_config_path(config_path)

    log.info("Formulating answer")
    report = WeatherReport(request, forecast)
    return report


def answer(weather_input, output, config_path: str = None):
    """
    Function that combines information into the form specified in config and outputs them to where is should go

    Args:
        weather_input: anything that a parser exists for
        output: either a WeatherReport or a WeatherError that contains information
        config_path: optional path to a config file

    Returns:
        output, unless one of the selected outputs has a specified return value. If there is one, it will return that instead

    """
    if config_path is not None and cf.config_path is not config_path:
        cf.set_config_path(config_path)

    config = cf.get_config()
    log.info("Answering")
    return_value = output
    for output_item in config.output:
        try:
            filled_template = fill_template(weather_input, output, output_item.get_template())
            return_value = output_item.output_response(filled_template)
        except (WeatherError, ConfigError) as e:
            log.error(f"Can't output response on {output_item.__name__}: {e.description}")

    return return_value
