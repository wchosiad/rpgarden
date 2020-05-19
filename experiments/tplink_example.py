import unittest
import requests
import uuid
import json
import random

# This example from https://logicalgenetics.com/controlling-a-tp-link-smart-bulb-with-python-and-requests/

USERNAME = 'your.email@address.com'
PASSWORD = 'YourPassword123'
 
 
class TpLinkApiTests(unittest.TestCase):
    def test_change_bulb_colour(self):
        # First step is to get a token by authenticating with your username (email) and password
        payload = {
            "method": "login",
            "params":
                {
                    "appType": "Kasa_Android",
                    "cloudUserName": USERNAME,
                    "cloudPassword": PASSWORD,
                    "terminalUUID": str(uuid.uuid4())
                }
        }
        response = requests.post("https://wap.tplinkcloud.com/", json=payload)
        self.assertEqual(200, response.status_code)
        obj = json.loads(response.content)
        token = obj["result"]["token"]
 
        # Find the bulb we want to change
        payload = {"method": "getDeviceList"}
        response = requests.post("https://wap.tplinkcloud.com?token={0}".format(token), json=payload)
        self.assertEqual(200, response.status_code)
 
        # The JSON returned contains a list of devices. You could filter by name etc, but here we'll just use the first
        obj = json.loads(response.content)
        bulb = obj["result"]["deviceList"][0]
 
        # The bulb object contains a 'regional' address for control commands
        app_server_url = bulb["appServerUrl"]
        # Also grab the bulbs ID
        device_id = bulb["deviceId"]
 
        # Send a command through to the bulb to change it's colour
        # This is the command for the bulb itself...
        bulb_command = {
            "smartlife.iot.smartbulb.lightingservice": {
                "transition_light_state": {
                    "on_off": 1,
                    "brightness": 100,
                    "hue": random.randint(1, 360), # Random colour
                    "saturation": 100
                }
            }
        }
        # ...which is escaped and passed within the JSON payload which we post to the API
        payload = {
            "method": "passthrough",
            "params": {
                "deviceId": device_id,
                "requestData": json.dumps(bulb_command)  # Request data needs to be escaped, it's a string!
            }
        }
        # Remember to use the app server URL, not the root one we authenticated with
        response = requests.post("{0}?token={1}".format(app_server_url, token), json=payload)
        self.assertEqual(200, response.status_code)
 
        # Hopefully the bulb just changed colour!
        print response.content