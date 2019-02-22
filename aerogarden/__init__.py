import logging
import urllib
import requests
import base64

import voluptuous as vol
from datetime import timedelta


from homeassistant.helpers.discovery import load_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_HOST
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'aerogarden'
SENSOR_PREFIX = 'aerogarden'
DATA_AEROGARDEN = 'AEROGARDEN'
DEFAULT_HOST = 'http://ec2-54-86-39-88.compute-1.amazonaws.com:8080'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN : vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)


class AerogardenAPI():

    def __init__(self, username, password, host=None):
        self._username = urllib.parse.quote(username)
        self._password = urllib.parse.quote(password)
        self._host = host
        self._userid = None
        self._error_msg = None
        self._data = None

        self._login_url = "/api/Admin/Login"
        self._status_url = "/api/CustomData/QueryUserDevice"
        self._update_url = "/api/Custom/UpdateDeviceConfig"

        self._headers = {
            "User-Agent" : "HA-Aerogarden/0.1",
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        self.login()

    @property
    def error(self):
       return self._error_msg

    def login(self):
 
        post_data = "mail=" + self._username + "&userPwd=" + self._password
        url = self._host + self._login_url

        try:
            r = requests.post(url, data=post_data, headers=self._headers)
        except RequestException:
            _LOGGER.exception("Error communicating with aerogarden servers")
            return False

        response = r.json()

        userid = response["code"]
        if userid > 0:
             self._userid = str(userid)
        else:
            self._error_msg = "Login api call returned %s" % (response["code"])

    def is_valid_login(self):
        if self._userid:
            return True

        return

    def garden_property(self, macaddr, field):

        if macaddr not in self._data:
            return None

        if field not in self._data[macaddr]:
            return None

        return self._data[macaddr][field]

    def light_toggle(self, macaddr):
        if macaddr not in self._data:
            return None

        post_data = { 
            "airGuid" : macaddr, 
            "chooseGarden" : self.garden_property(macaddr, "chooseGarden"), 
            "userID" : self._userid,
            "plantConfig" :  "{ \"lightTemp\" : %d }" % (self.garden_property(macaddr, "lightTemp"))
        }
        url = self._host + self._update_url

        try:
            r = requests.post(url, data=post_data, headers=self._headers)
        except RequestException:
            _LOGGER.exception("Error communicating with aerogarden servers")
            return False

        results = r.json()

        if "code" in results:
            if results["code"] == 1:
                return True

        self._error_msg = "Didn't get code 1 from update API call: %s" % (results["msg"])
        self.update(no_throttle=True)

        return False


    @property
    def gardens(self):
        return self._data.keys()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        data = {}
        if not self.is_valid_login():
            return 

        url = self._host + self._status_url
        post_data = "userID=" + self._userid

        try:
            r = requests.post(url, data=post_data, headers=self._headers)
        except RequestException:
            _LOGGER.exception("Error communicating with aerogarden servers")
            return False

        garden_data = r.json()

        if "Message" in garden_data:
            self._error_msg = "Couldn't get data for garden (correct macaddr?): %s" % (garden_data["Message"])
            return False

        for garden in garden_data:

            if "plantedName" in garden:
                garden["plantedName"] = \
                    base64.b64decode(garden["plantedName"]).decode('utf-8')

            gardenmac = garden["airGuid"]
            data[gardenmac] = garden

        self._data = data
        return True
       

def setup(hass, config):
    """ Setup the aerogarden platform """

    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    host = config[DOMAIN].get(CONF_HOST)

    ag = AerogardenAPI(username, password, host)
    if not ag.is_valid_login():
         _LOGGER.error("Invalid login: %s" % (ag.error))
         return

    ag.update()

    # store the aerogarden API object into hass data system
    hass.data[DATA_AEROGARDEN] = ag

    load_platform(hass, 'sensor', DOMAIN, {}, config)
    load_platform(hass, 'binary_sensor', DOMAIN, {}, config)
    load_platform(hass, 'light', DOMAIN, {}, config)

    return True

