from json import load
from os import environ
from time import sleep

from requests import post


od_service_url = environ.get('OD_SERVICE_URL')
prediction_url = f'{od_service_url}/predictions'
pause_duration = environ.get('PAUSE_DURATION', 5)


def get_payload():
    print('Loading payload.')
    with open('twodogs.json', 'rb') as payload_file:
        payload = load(payload_file)
    return payload


def do_request_loop(prediction_url, payload):
    while True:
        try:
            print(f'Sending request to {prediction_url}.')
            response = post(prediction_url, json=payload)
            print(f'Received response with status {response.status_code}.')
        except:
            print(f'Failed to receive response. Pausing for {pause_duration} seconds.')
            sleep(pause_duration)


if __name__ == '__main__':
    payload = get_payload()
    do_request_loop(prediction_url, payload)
