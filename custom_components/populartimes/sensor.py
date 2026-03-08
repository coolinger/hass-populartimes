"""Support for Google Places API."""
from datetime import datetime, timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.helpers.entity import Entity
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import homeassistant.helpers.config_validation as cv
import logging
import livepopulartimes
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

CONF_PLACE_ID = "place_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_PLACE_ID): cv.string,
    }
)

SCAN_INTERVAL = timedelta(minutes=10)

def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config[CONF_NAME]
    apikey = config[CONF_API_KEY]
    placeid = config[CONF_PLACE_ID]
    add_entities([PopularTimesSensor(name, apikey, placeid)], True)


class PopularTimesSensor(Entity):

    def __init__(self, name, apikey, placeid):
        self._name = name
        self._apikey = apikey
        self._placeid = placeid
        self._state = None

        self._attributes = {
            'maps_name': None,
            'place_id': placeid,
            'popularity_is_live': None,
            'popularity_monday': None,
            'popularity_tuesday': None,
            'popularity_wednesday': None,
            'popularity_thursday': None,
            'popularity_friday': None,
            'popularity_saturday': None,
            'popularity_sunday': None,
        }

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return "measurement"

    @property
    def unit_of_measurement(self):
        return '%'

    @property
    def state_attributes(self):
        return self._attributes

    def update(self):
        """Get the latest data from Google Places API."""
        try:
            result = livepopulartimes.get_populartimes_by_PlaceID(self._apikey, self._placeid)
            popularity = result.get('current_popularity', 0)

            self._attributes['maps_name'] = result["name"]
            self._attributes['popularity_monday'] = result["populartimes"][0]["data"]
            self._attributes['popularity_tuesday'] = result["populartimes"][1]["data"]
            self._attributes['popularity_wednesday'] = result["populartimes"][2]["data"]
            self._attributes['popularity_thursday'] = result["populartimes"][3]["data"]
            self._attributes['popularity_friday'] = result["populartimes"][4]["data"]
            self._attributes['popularity_saturday'] = result["populartimes"][5]["data"]
            self._attributes['popularity_sunday'] = result["populartimes"][6]["data"]

            dt = datetime.now()
            weekdayIndex = dt.weekday()
            hourIndex = dt.hour
            historicalDataForWeekday = result["populartimes"][weekdayIndex]["data"]
            historicalDataForHour = historicalDataForWeekday[hourIndex]

            if popularity != None:
               self._attributes['popularity_is_live'] = True

            if popularity == None:
                popularity = historicalDataForHour
                self._attributes['popularity_is_live'] = False
                _LOGGER.warning("Current popularity info is not live but based on historical data.")

            self._state = popularity

        except:
            _LOGGER.error("No popularity info is returned by the populartimes library.")
