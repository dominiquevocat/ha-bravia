"""
Support for interface with a Bravia TV.
v0.1 - still sucks. Need to modify code with the ip and mac address :-/
"""
import logging
import json
import requests
from requests.exceptions import ConnectionError
from wakeonlan import wol
from datetime import timedelta
import homeassistant.util as util

from homeassistant.components.media_player import (
    DOMAIN, SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP, SUPPORT_TURN_ON, SERVICE_TOGGLE,
    MediaPlayerDevice) 
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN)
from homeassistant.helpers import validate_config

CONF_PORT = "port"
CONF_TIMEOUT = "timeout"

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['wakeonlan==0.2.2']
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(milliseconds=100)

SUPPORT_BRAVIA = SUPPORT_PAUSE | SUPPORT_VOLUME_STEP | \
    SUPPORT_VOLUME_MUTE | SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_NEXT_TRACK | SUPPORT_TURN_ON | SUPPORT_TURN_OFF


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Bravia TV platform."""
    # Validate that all required config options are given
    if not validate_config({DOMAIN: config}, {DOMAIN: [CONF_HOST]}, _LOGGER):
        return False

    # Default the entity_name to 'MyBraviaTV'
    name = config.get(CONF_NAME, 'MyBraviaTV')
    host = config.get(CONF_HOST)
    timeout = config.get(CONF_TIMEOUT, 0.001)

    # Generate a config for the Bravia
    remote_config = {
        "name": "HomeAssistant",
        "description": config.get(CONF_NAME, ''),
        "id": "ha.component.bravia",
        "host": config.get(CONF_HOST),
        "timeout": config.get(CONF_TIMEOUT, 0),
    }

    add_devices([BraviaTVDevice(name, remote_config)])


# pylint: disable=abstract-method
class BraviaTVDevice(MediaPlayerDevice):
    """Representation of a Bravia TV."""

    # pylint: disable=too-many-public-methods
    def __init__(self, name, config):
        """Initialize the Sony device."""
        self._name = name
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._state = STATE_UNKNOWN #STATE_OFF
        self._remote = None
        self._config = config
    
    @classmethod
    def do_ircc(self, data):
        sony_xml = \
        """<?xml version="1.0"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
          <s:Body>
            <u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1">
              <IRCCCode>%s</IRCCCode>
            </u:X_SendIRCC>
          </s:Body>
        </s:Envelope>"""
        try:
            req = requests.request('POST', 'http://192.168.0.12/sony/IRCC/',
                               headers={'SOAPAction': "urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"},
                               timeout=0.1,
                               data=sony_xml % data)
            print("sending " + data + " to the TV. We got a reply from the TV and assume its on " + str(req))
            self._state = STATE_ON
            return True
        except:    #ConnectionError as e - This is the correct syntax
            #print(e)
            print("sending " + data + " to the TV. We got an error contacting the tv - we assume its off ")
            self._state = STATE_OFF
            return False
        """
        req = requests.request('POST', 'http://192.168.0.12/sony/IRCC/',
                               headers={'SOAPAction': "urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"},
                               data=sony_xml % data)
        """
        #return req
    
    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)    
    def update(self):
        """Retrieve the latest data."""
        # Send an empty key to see if we are still connected
        #return self.do_ircc('*SEPOWR################') #AAAAAQAAAAEAAABlAw== -> confirm
        print("updating state of the bravia tv")
        try:
            #print("check for tv...")
            req = requests.request('GET', 'http://192.168.0.12/', timeout=0.001)
        except:
            #print("nah")
            self._state = STATE_OFF
            return False
        else:
            #print("yeah")
            self._state = STATE_ON
            return True

    def send_key(self, key):        
        return True

    
    @property
    def toggle(self):
        if self._state == STATE_OFF:
            self.turn_on()
        elif self_state == STATE_UNKNOWN:
            self.turn_on()
        else:
            self.turn_off()
    
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_BRAVIA

    def turn_on(self):
        """Turn the media player on."""
        #self.do_ircc('AAAAAQAAAAEAAAAAAw==') #PowerOn i guess would be AAAAAQAAAAEAAAAVAw== so we send channel one
        print("sending magic packet to turn on tv")
        self._state = STATE_ON
        wol.send_magic_packet('d8d43ccf8f9d')
        
    def turn_off(self):
        """Turn off media player."""
        print("turn off tv")
        self._state = STATE_OFF
        return self.do_ircc('AAAAAQAAAAEAAAAvAw==') #power off

    def volume_up(self):
        """Volume up the media player."""
        return self.do_ircc('AAAAAQAAAAEAAAASAw==') #VolumeUp

    def volume_down(self):
        """Volume down media player."""
        return self.do_ircc('AAAAAQAAAAEAAAATAw==') #VolumeDown

    def mute_volume(self, mute):
        """Send mute command."""
        return self.do_ircc('AAAAAQAAAAEAAAAUAw==') #Mute

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        self._playing = True
        #self.send_key("KEY_PLAY")

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        #self.send_key("KEY_PAUSE")

    def media_next_track(self):
        """Send next track command."""
        #self.send_key("KEY_FF")
        #hack for trying out the turn on WoL feature - disregard
        print("sending magic packet to turn on tv d8d43ccf8f9d")
        wol.send_magic_packet('d8d43ccf8f9d')

    def media_previous_track(self):
        """Send the previous track command."""
        #self.send_key("KEY_REWIND")
