import requests
import os

BASE_URL = 'http://127.0.0.1:8000'


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
