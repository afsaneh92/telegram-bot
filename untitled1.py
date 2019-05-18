from pymongo import MongoClient
import pprint
from flask import Flask, request
import requests

send_message_url = "https://api.telegram.org/bot547599953:AAFwSfxhy4yXMSOpIgqQgLweHZsjK1uLZLs/sendMessage"

app = Flask(__name__)


def initialize():
    global state_dict
    global db

    state_dict = {}

    db = MongoClient().locationdb


@app.route('/updateme', methods=['POST'])
def response():
    global state_dict

    update = request.json
    print update

    userId = update['message']['from']['id']
    if not userId in state_dict.keys():
        state_dict[userId] = {"state": "idle", "location": None, "maxDis": None}

    if state_dict[userId]['state'] == "idle":
        handle_idle_state(update)

    elif state_dict[userId]['state'] == "wait":
        handle_wait_state(update)
        if state_dict[userId]['state'] == "geolocation":
            find_iws(update)

    print state_dict
    return 'ok'


def handle_wait_state(update):
    global state_dict

    userId = update['message']['from']['id']
    if 'text' in update['message'].keys():
        try:
            state_dict[userId]['maxDis'] = float(update['message']['text'])
            state_dict[userId]['state'] = "geolocation"
        except ValueError:
            requests.post(send_message_url, data={'chat_id': update['message']['chat']['id'],
                                                  'text': 'Invalid number! please give me number'})

            state_dict[userId]['state'] = "wait"
    else:
        requests.post(send_message_url,
                      data={'chat_id': update['message']['chat']['id'], 'text': 'please give me number'})

        state_dict[userId]['state'] = "wait"


def handle_idle_state(update):
    global state_dict

    userId = update['message']['from']['id']
    if 'location' in update['message'].keys():
        state_dict[userId]['location'] = update['message']['location']['latitude'], update['message']['location'][
            'longitude']

        requests.post(send_message_url,
                      data={'chat_id': update['message']['chat']['id'], 'text': 'please give me max distance'})

        state_dict[userId]['state'] = "wait"
    else:
        requests.post(send_message_url,
                      data={'chat_id': update['message']['chat']['id'], 'text': 'please send me your location'})

        state_dict[userId]['state'] = "idle"


def find_iws(update):
    global state_dict
    global db

    userId = update['message']['from']['id']
    location_cursor = db.mycollection.find(
        {"location":
             {"$near":
                  {"$geometry": {"type": "Point", "coordinates": state_dict[userId]['location']},
                   "$maxDistance": state_dict[userId]['maxDis']}}
         }, {"name": 1, "_id": 0})
    mylist = list(location_cursor)
    for doc in mylist:
        requests.post(send_message_url,
                      data={'chat_id': update['message']['chat']['id'], 'text': doc['name']})
    state_dict[userId]['state'] = "idle"


if __name__ == '__main__':
    initialize()
    app.run()
