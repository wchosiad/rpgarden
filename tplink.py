import requests            # HTTP Request library. see https://2.python-requests.org/en/master/api/
import json

device_id = '8006FDBA9BE7E8A0643794E14112EBBE186980D2'
app_server_url = 'https://use1-wap.tplinkcloud.com'
token = 'd135dc22-A5scRCQptnNRlDQQO6UCFaf'

def setLight(onOff) :
    # onOff - Set True to turn switch on, False to turn switch off
    _response = {}
    newState = 0
    if onOff:
        newState = 1

    switch_command = {
        "system" : {
            "set_relay_state" : {
                "state" : newState 
            }
        }
    }
    # ...which is escaped and passed within the JSON payload which we post to the API
    payload = {
        "method": "passthrough",
        "params": {
            "deviceId": device_id,
            "requestData": json.dumps(switch_command)  # Request data needs to be escaped, it's a string!
        }
    }
    # Remember to use the app server URL, not the root one we authenticated with
    _response = requests.post("{0}?token={1}".format(app_server_url, token), json=payload)
    return _response


myResponse = setLight(True)
print(myResponse)
print(myResponse.text)
