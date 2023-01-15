import requests
import os

BASE_URL = 'http://api:8000'
HEADERS = {'accept': 'application/json'}


def get_list_dbs():
    url = f"{BASE_URL}/dbs"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def get_translate(question: str, db_id: str):
    url = f"{BASE_URL}/ask/{db_id}/{question}"
    response = requests.get(url, headers=HEADERS)
    return response.json()


def upload(file: bytes):
    url = f"{BASE_URL}/upload/"
    resp = requests.post(url=url, data=file, headers={
                         'Content-Type': 'application/octet-stream'})
    return resp.text


def proxy_mysql(config):
    url = f"{BASE_URL}/proxy/"
    connection_string = f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    response = requests.post(url, json=connection_string)
    return response.text
