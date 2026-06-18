import os
import requests
import unittest
from dotenv import load_dotenv
from loguru import logger
from ..utils.http_utils import parse_response


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        cls.host = "https://zebin123-omnihub.hf.space"
        logger.info(f"Service Host: {cls.host}")
        cls.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN_READONLY')}"}

    def test_read_root(self):
        url = f"{self.host}/"
        rsp = requests.get(url, headers=self.headers)
        parse_response(rsp)
