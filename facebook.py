#import Facebook_scraper class from facebook_page_scraper
from facebook_page_scraper import Facebook_scraper
import json
import logging
import requests
import sys
import time

import os
import re
import traceback
from urllib.parse import unquote
import hashlib

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def set_default(obj):
	if isinstance(obj, set):
		return list(obj)
	raise TypeError

def download_file(url, path, proxy=None, cookies=None):
	try:
		# If a proxy was provided, use it, otherwise make a direct request
		if proxy:
			response = requests.get(url, stream=True, verify=False, proxies={"http": proxy, "https": proxy}, cookies=cookies)
		else:
			response = requests.get(url, stream=True, verify=False, cookies=cookies)

		# Check the status code of the response
		if response.status_code == 200:
			# Extract filename from Content-Disposition header
			content_disposition = response.headers.get('content-disposition')
			print(response)
			if content_disposition:
				filename = re.findall('filename=(.+)', content_disposition)[0]
				filename = unquote(filename)  # Decode URL-encoded string
			else:
				filename = url.split("/")[-1]  # Default filename if no Content-Disposition header is found

			# Calculate the MD5 hash of the URL
			md5_hash = hashlib.md5(url.encode())

			# Add MD5 hash to the filename
			filename_md5 = md5_hash.hexdigest() + '.jpg'
			filepath = os.path.join(path, filename_md5)

			# Check if the file already exists
			if os.path.isfile(filepath):
				logger.info(f"File {filename_md5} already exists. No need to download.")
				return filename_md5

			# Open the file in write mode
			with open(filepath, 'wb') as file:
				for chunk in response.iter_content(chunk_size=8192):
					file.write(chunk)

			logger.info(f"File {filename_md5} downloaded successfully.")
			return filename_md5
		else:
			logger.error(f"Failed to download the file. HTTP Status Code: {response.status_code}")
			return None
	except Exception as e:
		logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")
		return None

headers = {
	'Content-Type': 'application/json',
}

#instantiate the Facebook_scraper class

page_or_group_name = sys.argv[1]
posts_count = 5
browser = "undetected-chromedriver"
proxy = "195.158.2.216:18001" #if proxy requires authentication then user:password@IP:PORT
timeout = 600 #600 seconds
headless = False
# get env password
fb_password = os.getenv('fb_password')
fb_email = os.getenv('fb_email')
# indicates if the Facebook target is a FB group or FB page
isGroup= False
meta_ai = Facebook_scraper(page_or_group_name, posts_count, browser, proxy=proxy, timeout=timeout, headless=headless, isGroup=isGroup,
	profile='/var/www/medusa/modules/facebookV4/chrome', user_agent='Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', cookies="valid.json")

# change_language = meta_ai.edit_language()
# print(change_language)

# page_info = meta_ai.scrape_user_data()
# print(page_info)

# list_cookies = meta_ai.get_cookies()
# print(list_cookies)

RUNNER_POSTS = meta_ai.scrap_to_json()

POSTS_JSON = json.loads(RUNNER_POSTS)

for key in POSTS_JSON:
	value = POSTS_JSON[key]
	logger.info(f'Post #{key} date: {value["posted_on"]}')
	value['task_id'] = sys.argv[2]
	if 'images' in value:
		z = []
		for image in value["images"]:
			z.append(download_file(image, "C:/Users/1/Desktop/PARSERS/FACEBOOK/images","socks5://your_dante_user:your_dante_password@195.158.2.216:10080"))
			value["media"] = z

response = requests.post('http://192.168.30.215/api/facebook/v4/store', headers=headers, json=POSTS_JSON)

print(POSTS_JSON)