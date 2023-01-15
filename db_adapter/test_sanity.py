import requests
import unittest
import os


class TestSanity(unittest.TestCase):

    def test_proxy_mysql(self):
        url = "http://127.0.0.1:8000/proxy/"
        config = {
            "host": "mysql",
            "port": 3306,
            "user": "root",
            "password": "root",
            "database": "Chinook",
        }
        response = requests.post(
            url, json=f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}")
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
