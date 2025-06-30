import os
import subprocess
import json

def battery_check ():
    try :
        battery_termux = subprocess.check_output(["termux-battery-status"])
        battery = json.load(battery_termux)
        return int(battery["percentage"])

    except Exception as e :
        logging.debug("error has occured" , e)
        return 100


def if_battery_low (threshold = 5):
    return battery_check <= threshold
