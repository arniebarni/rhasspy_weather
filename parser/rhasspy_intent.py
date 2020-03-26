import datetime
from rhasspy_weather.data_types.request import WeatherRequest, DateType, ForecastType, Grain
from rhasspy_weather.data_types.status import Status, StatusCode
from rhasspy_weather.data_types.location import Location
from rhasspy_weather.locale.german import named_days, weekday_names, month_names, named_times, named_times_synonyms

import logging

log = logging.getLogger(__name__)

def parse_intent_message(intent_message, config):
    intent = None
    
    # if you changed the slot names in rhasspy, change them here, too
    slot_day_name = "when_day"
    slot_time_name = "when_time"
    slot_location_name = "location"
    slot_item_name = "item"
    slot_condition_name = "condition"
    slot_temperature_name = "temperature"
    
    if "GetWeatherForecastCondition" == intent_message["intent"]["name"]:
        intent = ForecastType.CONDITION
    elif "GetWeatherForecastItem" == intent_message["intent"]["name"]:
        intent = ForecastType.ITEM
    elif "GetWeatherForecastTemperature" == intent_message["intent"]["name"]:
        intent = ForecastType.TEMPERATURE
    elif  "GetWeatherForecast" == intent_message["intent"]["name"]:
        intent = ForecastType.FULL
    
    # date and time
    today = datetime.datetime.now(config.timezone).date()
    #define default request
    new_request = WeatherRequest(DateType.FIXED, Grain.DAY, today, intent, config)

    # if a day was specified
    slots = intent_message["slots"]
    if slot_day_name in slots and slots[slot_day_name] != "":
        log.debug("it was a day specified")
        named_days_lowercase = [x.lower() for x in named_days]
        weekdays_lowercase = [x.lower() for x in weekday_names]
        # is it a named day (tomorrow, etc.)?
        if slots[slot_day_name].lower() in named_days_lowercase:
            log.debug("  named day detected")
            index = named_days_lowercase.index(slots[slot_day_name].lower())
            key = list(named_days.keys())[index]
            value = list(named_days.values())[index]
            if isinstance(value, datetime.date):
                log.debug("    named day seems to be a date")
                self.status.set_status(StatusType.NOT_IMPLEMENTET_ERROR)
            elif isinstance(value, int):
                log.debug("    named day seems to be an offset from today")
                new_request.request_date = datetime.date.today() + datetime.timedelta(value)
                new_request.date_specified = key
        # is a weekday named?
        elif slots[slot_day_name].lower() in weekdays_lowercase:
            log.debug("  weekday detected")
            index = weekdays_lowercase.index(slots[slot_day_name].lower())
            name = weekday_names[index]
            for x in range(7):
                new_date = today + datetime.timedelta(x)
                if slots[slot_day_name].lower() == weekdays_lowercase[new_date.weekday()]:
                    new_request.request_date = new_date
                    new_request.date_specified = "am " + name
                    break
        # was a date specified (specified by rhasspy as "daynumber monthname")?
        elif ' ' in slots[slot_day_name]:
            log.debug("  date detected")
            day, month = slots[slot_day_name].split()
            months_lowercase = [x.lower() for x in month_names]
            if month.lower() in months_lowercase:
                index = months_lowercase.index(month.lower())
                name = month_names[index]
                new_request.date_specified = "am " + day + ". " + name
                # won't work when the year changes, fix that sometime
                try:
                    new_request.request_date = datetime.date(datetime.date.today().year, index+1, int(day))
                except ValueError:
                    new_request.status.set_status(StatusCode.DATE_ERROR)
        
        # if a time was specified
        if slot_time_name in slots and slots[slot_time_name] != "":
            log.debug("it was a time specified")
            new_request.grain = Grain.HOUR
            
            named_times_lowercase = [x.lower() for x in named_times]
            named_times_synonyms_lowercase = [x.lower() for x in named_times_synonyms]
            named_times_combined = named_times_lowercase + named_times_synonyms_lowercase
            # was something like midday specified (listed in named_times or in named_times_synonyms)?
            if isinstance(slots[slot_time_name], str) and slots[slot_time_name].lower() in named_times_combined:
                log.debug("  named time frame detected")
                if slots[slot_time_name].lower() in named_times_synonyms_lowercase:
                    index = named_times_synonyms_lowercase.index(slots[slot_time_name].lower())
                    name = list(named_times_synonyms.keys())[index]
                    value = named_times[named_times_synonyms[name]]
                else:
                    index = named_times_lowercase.index(slots[slot_time_name].lower())
                    name = list(named_times.keys())[index]
                    value = list(named_times.values())[index]
                log.debug(value)
                if isinstance(value, datetime.time):
                    log.debug("    named time seems to be a certain time")
                    self.status.set_status(StatusType.NOT_IMPLEMENTET_ERROR)
                elif isinstance(value, tuple):
                    log.debug("    named time seems to be an interval")
                    new_request.date_type = DateType.INTERVAL
                    new_request.start_time = value[0]
                    new_request.end_time = value[1]
                    new_request.time_specified = name
            # was it hours and minutes (specified as "HH MM" by rhasspy intent)?
            elif isinstance(slots[slot_time_name], str) and ' ' in slots[slot_time_name]:
                log.debug("    hours and minutes detected")
                new_request.start_time = datetime.datetime.strptime(slots[slot_time_name], '%H %M').time()
                new_request.time_specified = "um " + str(new_request.start_time.hour) + " Uhr " + str(new_request.start_time.minute)
            # is it only an hour (no way to only specify minutes, if it is an int, it is hours)?
            elif isinstance(slots[slot_time_name], int):
                log.debug("    hours detected")
                new_request.start_time = datetime.time(slots[slot_time_name], 0)
                new_request.time_specified = "um " + str(new_request.start_time.hour) + " Uhr"
            else:
                new_request.grain = Grain.DAY
        else:
            log.debug("no time specified, getting weather for the full day")
    else:
        log.debug("no day specified, using today as default")
    
    # requested
    requested = None
    if intent == ForecastType.CONDITION and slot_condition_name in slots:
        requested = slots[slot_condition_name]
    elif intent == ForecastType.ITEM and slot_item_name in slots:
        requested = slots[slot_item_name]
    elif intent == ForecastType.TEMPERATURE and slot_temperature_name in slots:
        requested = slots[slot_temperature_name]
    if not requested == None:
        log.debug("there was a special request made")
        new_request.requested = requested.capitalize() # first letter uppercase because german nouns just are that way (and the weather_logic will break)

    # location
    if slot_location_name in slots:
        log.debug("a location was specified")
        new_request.location = Location(slots[slot_location_name])
                
    return new_request