from flask import Flask
from flask import request
from  flask import jsonify
# from flask_sslify import SSLify
import requests
import json
import re
from datetime import datetime, timedelta


app = Flask(__name__)
# sslify = SSLify(app)


try:
    from app.settings_local import * # noqa
except ImportError:
    pass


# https://api.telegram.org/bot<token>/METHOD_NAME

URL = 'https://api.telegram.org/bot' + token +'/'


global last_request_time
last_request_time = datetime.now() - timedelta(minutes=11)


def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_json(filename_json):
    with open(filename_json) as data_file:
        return json.load(data_file)


def send_message(chat_id, text='bla-bla-bla'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=answer)
    return r.json()


# https://api.exchangeratesapi.io/latest?base=USD
def get_rate_list():
    url = 'https://api.exchangeratesapi.io/latest?base=USD'

    response = requests.get(url).json()  # dict
    rate_dict = response['rates']  # dict

    return '\n'.join([f'{i}: {round(j, 2)}' for i, j in rate_dict.items()])


def parse_text(text):
    pattern = r'/exchange \d{2} \w{3} to \w{3}'
    print(re.search(pattern, text))
    try:
        crypto = re.search(pattern, text).group()
        print(crypto)
        print(crypto[10:12],crypto[13:16], crypto[20:])
        return int(crypto[10:12]), crypto[13:16], crypto[20:]
    except:
        return None


def get_converted_price(quantity, coin_1, coin_2):
    # url = 'https://api.exchangeratesapi.io/latest?base=USD'
    url = 'https://api.exchangeratesapi.io/latest?base={}'.format(coin_1)
    try:
        response = requests.get(url).json()  # dict
        rate_dict = response['rates']  # dict
        price = round(rate_dict[coin_2] * quantity, 2)
        # write_json(response, filename='price.json')
        return f'{coin_2} {price}'
    except:
        return 'Not found'


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        r = request.get_json()

        chat_id = r['message']['chat']['id']
        message = r['message']['text']

        pattern = r'/exchange \d{2} \w{3} to \w{3}'

        # if message == '/lst' or message == '/list':
        if '/lst' in message or '/list' in message:
            global last_request_time
            # print(last_request_time)
            current_time = datetime.now()
            # print(current_time)
            if  (current_time - last_request_time) <= timedelta(minutes=10):
                last_request_time = current_time
                # print(last_request_time)
                send_message(chat_id, read_json('rate_list.json'))
            else:
                data = get_rate_list()
                write_json(data, filename='rate_list.json')
                last_request_time = current_time
                send_message(chat_id, data)


        if re.search(pattern, message):
            price = get_converted_price(*parse_text(message))
            send_message(chat_id, price)

        return jsonify(r)
    return '<h1>Bot welcomes you</h1>'


if __name__ == '__main__':
    app.run()
