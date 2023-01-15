import requests
import unittest
import os


class TestSanity(unittest.TestCase):

    def test_upload(self):
        url = 'http://127.0.0.1:8000/upload/'
        file = open(os.path.join(
            os.path.dirname(__file__), 'test_file.txt'), 'rb')
        resp = requests.post(url=url, data=file, headers={
                             'Content-Type': 'application/octet-stream'})
        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
