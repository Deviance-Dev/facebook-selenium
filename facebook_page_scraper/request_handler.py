#!/usr/bin/env python3

from curl_cffi import requests
from selectolax.parser import HTMLParser
import json
import sys

import logging
import re

logger = logging.getLogger(__name__)
format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)

class RequestHandler:

    @staticmethod
    def __fetch_html(url: str) -> str:
        """
        Fetches the HTML content from the given URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: HTML content of the page.

        Raises:
            SystemExit: If there's an error fetching the page.
        """

        head_req = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }

        try:
            response = requests.get(url, headers=head_req)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching the page [{url}]: {e}")
            sys.exit(1)

    @staticmethod
    def __parse_json_from_html(html_content: str, key_to_find: str) -> dict:
        """
        Parses JSON data from HTML by extracting the relevant script block.

        Args:
            html_content (str): The raw HTML content of the page.
            key_to_find (str): The key to look for in the script.

        Returns:
            dict: The parsed JSON object.

        Raises:
            SystemExit: If no valid data is found or parsing fails.
        """
        try:
            parser = HTMLParser(html_content)
            for script in parser.css('script[type="application/json"]'):
                script_text = script.text(strip=True)
                if key_to_find in script_text:
                    return json.loads(script_text)
            print(f"No valid data found for key '{key_to_find}' in the HTML page.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for key '{key_to_find}': {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error parsing JSON for key '{key_to_find}': {e}")
            sys.exit(1)