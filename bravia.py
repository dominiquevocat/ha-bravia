"""
Support for interface with a Bravia TV.
Version 0.3
"""
import logging
import json
import requests
from requests.exceptions import ConnectionError
from wakeonlan import wol
from datetime import timedelta
import homeassistant.util as util
from time import sleep

from homeassistant.components.media_player import (
    DOMAIN, SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP,
    SUPPORT_TURN_ON, SERVICE_TOGGLE, SUPPORT_SELECT_SOURCE,
    MediaPlayerDevice) 
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN)
from homeassistant.helpers import validate_config
from homeassistant.components import discovery

CONF_PORT = "port"
CONF_TIMEOUT = "timeout"
CONF_MAC = "mac"
CONF_PSK = "psk"

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['wakeonlan==0.2.2']
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(milliseconds=100)

SUPPORT_BRAVIA = SUPPORT_PAUSE | SUPPORT_VOLUME_STEP | \
    SUPPORT_VOLUME_MUTE | SUPPORT_PREVIOUS_TRACK | \
    SUPPORT_NEXT_TRACK | SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Bravia TV platform."""
    #discovery
    if discovery_info is not None:
        #_LOGGER.debug('%s', discovery_info)
        print(discovery_info)
        print(type(discovery_info))
        name = 'MyBraviaTV' #discovery_info[0]
        host = discovery_info[1]
        mac  = discovery_info[2]
        _LOGGER.debug("we found a device with info: " + name + " " + host + " " + mac)
        #timeout = config.get(CONF_TIMEOUT, 0.001)
        add_devices([BraviaTVDevice(name, discovery_info)])
        return True
    # Default the entity_name to 'MyBraviaTV', use host and mac property from conf
    else:
        name = config.get(CONF_NAME, 'MyBraviaTV')
        host = config.get(CONF_HOST)
        mac  = config.get(CONF_MAC) #'d8d43ccf8f9d'
        psk  = config.get(CONF_PSK) #how about 8123 ?
    
    # Validate that all required config options are given - off for now

# pylint: disable=abstract-method
class BraviaTVDevice(MediaPlayerDevice):
    """Representation of a Bravia TV."""

    # pylint: disable=too-many-public-methods
    def __init__(self, name, config):
        """Initialize the Sony device."""
        print("setting up the device Bravia")
        print(config)
        self._name = name
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._state = STATE_UNKNOWN #STATE_OFF
        self._remote = None
        self._config = config
        self._host = config[1]
        self._mac = config[2]
        _LOGGER.debug("set up tv as follows: ip:" + self._host + " - mac:" + self._mac)
    
    @classmethod
    def do_ircc(self, host, data):
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
            req = requests.request('POST', 'http://'+ host +'/sony/IRCC/',
                               headers={'SOAPAction': "urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"},
                               timeout=0.1,
                               data=sony_xml % data)
            _LOGGER.debug("sending " + data + " to the TV at "+host+". We got a reply from the TV and assume its on " + str(req))
            self._state = STATE_ON
            return True
        except:
            _LOGGER.debug("sending " + data + " to the TV at "+host+". We got an error contacting the tv - we assume its off ")
            self._state = STATE_OFF
            return False
    
    @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)    
    def update(self):
        """Retrieve the latest data."""
        try:
            _LOGGER.debug('check for tv... http://'+self._host+'/')
            req = requests.request('GET', 'http://'+self._host+'/', timeout=0.1)
        except:
            self._state = STATE_OFF
            return False
        else:
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
        #self.do_ircc(self._host,'AAAAAQAAAAEAAAAAAw==') #PowerOn i guess would be AAAAAQAAAAEAAAAVAw== so we send channel one
        _LOGGER.debug("sending magic packet to '+self._mac+' to turn on tv")
        self._state = STATE_ON
        wol.send_magic_packet(self._mac)
        
    def turn_off(self):
        """Turn off media player."""
        print("turn off tv")
        self._state = STATE_OFF
        return self.do_ircc(self._host,'AAAAAQAAAAEAAAAvAw==') #power off

    def volume_up(self):
        """Volume up the media player."""
        return self.do_ircc(self._host,'AAAAAQAAAAEAAAASAw==') #VolumeUp

    def volume_down(self):
        """Volume down media player."""
        return self.do_ircc(self._host,'AAAAAQAAAAEAAAATAw==') #VolumeDown

    def mute_volume(self, mute):
        """Send mute command."""
        return self.do_ircc(self._host,'AAAAAQAAAAEAAAAUAw==') #Mute

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

    def media_previous_track(self):
        """Send the previous track command."""
        #self.send_key("KEY_REWIND")
        
    def select_source(self, source):
        """Set the input source."""
        # test like this: {"entity_id":"media_player.mybraviatv","source":"1 SF DRS"}
        """
        The commands for the numbers 0 to 9 are as follows:
        'Num0': 'AAAAAQAAAAEAAAAJAw==',
        'Num1': 'AAAAAQAAAAEAAAAAAw==',
        'Num2': 'AAAAAQAAAAEAAAABAw==',
        'Num3': 'AAAAAQAAAAEAAAACAw==',
        'Num4': 'AAAAAQAAAAEAAAADAw==',
        'Num5': 'AAAAAQAAAAEAAAAEAw==',
        'Num6': 'AAAAAQAAAAEAAAAFAw==',
        'Num7': 'AAAAAQAAAAEAAAAGAw==',
        'Num8': 'AAAAAQAAAAEAAAAHAw==',
        'Num9': 'AAAAAQAAAAEAAAAIAw==',
        """
        dial = str(source.split(' ')[0])
        _LOGGER.debug("set source to " + dial)        
        for c in dial: #dialing 0118 999 881 999 119 7253
            if c == "0":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAJAw==')
            if c == "1":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAAAw==')
            if c == "2":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAABAw==')
            if c == "3":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAACAw==')
            if c == "4":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAADAw==')
            if c == "5":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAEAw==')
            if c == "6":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAFAw==')
            if c == "7":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAGAw==')
            if c == "8":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAHAw==')
            if c == "9":
                self.do_ircc(self._host,'AAAAAQAAAAEAAAAIAw==')
            sleep(0.25) # sleep a bit in order to send all keys properly
