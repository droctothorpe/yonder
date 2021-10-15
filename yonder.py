import configparser
import geocoder
import logging
import os
from pyowm import OWM
import rumps
from threading import Thread
from time import sleep
from typing import Tuple

config = configparser.ConfigParser()
path = os.path.expanduser("~") + '/.config/yonder/yonder.ini'


def initialize_config():
    if not os.path.exists(path):
        logging.debug(f"Config file not found. Writing default config to {path}.")
        config['yonder'] = {
            'min': 50,
            'max': 75,
            'interval': 60,
            'good_icon': '☀︎',
            'bad_icon': '⧄',
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        config.write(open(path, 'w'))


initialize_config()


class Yonder(rumps.App):
    def __init__(self):
        super(Yonder, self).__init__('Yonder')

        config.read(path)
        self.min = int(config.get('yonder', 'min'))
        self.max = int(config.get('yonder', 'max'))
        self.interval = int(config.get('yonder', 'interval'))
        self.good_icon = config.get('yonder', 'good_icon')
        self.bad_icon = config.get('yonder', 'bad_icon')
        self.title = self.bad_icon
        self.update_weather()

    def update_weather(self):
        def callback_thread():
            # sleep(3)
            while True:
                good, feels_like = check_weather(self.min, self.max)
                if good:
                    self.title = self.good_icon
                    logging.debug("Weather is good")
                else:
                    self.title = self.bad_icon
                    logging.debug("Weather is bad")
                self.menu['feels_like'] = f"Feels like: {round(feels_like)}°F"

                sleep(self.interval)

        t = Thread(target=callback_thread, daemon=True)
        t.start()


def check_weather(min: int, max: int) -> Tuple[bool, int]:
    """
    Retrieve weather data and return go outside bool and feels like. 
    """
    g = geocoder.ip('me')
    logging.debug(g.latlng)

    # OWM interactions
    owm = OWM("4aa9747030fac3467a90683a19f43738")
    mgr = owm.weather_manager()

    oc = mgr.one_call(
        lat=g.latlng[0],
        lon=g.latlng[1],
        exclude='minutely',
        units='imperial')

    feels_like = oc.current.temp['feels_like']
    prob_rain_one = oc.forecast_hourly[0].precipitation_probability
    prob_rain_two = oc.forecast_hourly[1].precipitation_probability
    logging.debug(f"Feels like: {feels_like}")

    if min <= feels_like <= max and prob_rain_one <= 50 and prob_rain_two <= 50:
        return True, feels_like
    else:
        return False, feels_like


if __name__ == '__main__':
    # rumps.debug_mode(True)
    Yonder().run()
