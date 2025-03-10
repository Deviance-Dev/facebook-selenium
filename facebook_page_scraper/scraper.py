#!/usr/bin/env python3
import csv
import json
import logging
import os
import time
from selenium.common import exceptions

from .driver_initialization import Initializer
from .driver_utilities import Utilities
from .element_finder import Finder
from .scraping_utilities import Scraping_utilities
from .request_handler import RequestHandler
from .user_data_scraper import UserDataScraper

logger = logging.getLogger(__name__)
format = logging.Formatter(
		"%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)

class Facebook_scraper:

		# when we scroll and extract all posts,it may happens that we extract same posts over and over,so this lead to too much iteration
		# and waste time to iterate over and over the same post, to solve that,
		# problem I needed a data structure which
		# 1) removes duplicates from itself automatically,
		# 2) provides search of element,
		# 3) compatible with list's unpacking to quickly add element inside itself from list
		#  set() seems to be doing the work properly

		# condition,
		# 1) if we reach bottom of the page and post is not longer available, and we don't meet the number of posts that we need to find
		# 2) if we were given wrong page_or_group_name, and it does not exists in fb than no post will exist.
		# with above condition being true, the crawler will keep on scrolling the page to find posts
		# and it will stuck in infinite loop, which may cause machine to crash
		# to solve the problem, I have declared a class member "retry",assigned it value 10.
		# it checks 'retry' times if posts does not exists.
		# __no_post_found method subtracts -1 every time the if post is not found.
		# on each iteration __close_after_retry is called to check if retry have turned to 0
		# if it returns true,it will break the loop. After coming out of loop,driver will be closed and it will return post whatever was found

		def __init__(self, page_or_group_name, posts_count=10, browser="chrome", proxy=None, profile=None, user_agent=None,
								 timeout=600, headless=True, isGroup=False, username=None, password=None, cookies=None):
				self.page_or_group_name = page_or_group_name
				self.posts_count = int(posts_count)
				#self.URL = "https://en-gb.facebook.com/pg/{}/posts".format(self.page_or_group_name)
				self.URL = "https://facebook.com/{}".format(self.page_or_group_name)
				self.browser = browser
				self.__driver = ''
				self.proxy = proxy
				self.profile = profile
				self.user_agent = user_agent
				self.__layout = ''
				self.timeout = timeout
				self.headless = headless
				self.isGroup = isGroup
				self.username = username
				self.password = password
				self.cookies = cookies
				self.__data_dict = {}  # this dictionary stores all post's data
				# __extracted_post contains all the post's ID that have been scraped before and as it set() it avoids post's ID duplication.
				self.__extracted_post = set()

		def __start_driver(self):
				"""changes the class member __driver value to driver on call"""
				self.__driver = Initializer(
						self.browser, self.proxy, self.headless, self.profile, self.user_agent).init()

		def __handle_popup(self, layout):
				# while scrolling, wait for login popup to show, it can be skipped by clicking "Not Now" button
				try:
						if layout == "old":
								# if during scrolling any of error or signup popup shows
								Utilities._Utilities__close_error_popup(self.__driver)
								Utilities._Utilities__close_popup(self.__driver)
						elif layout == "new":
								Utilities._Utilities__close_modern_layout_signup_modal(
										self.__driver)
								Utilities._Utilities__close_cookie_consent_modern_layout(
										self.__driver)

				except Exception as ex:
						logger.exception("Error at handle_popup : {}".format(ex))

		def __check_timeout(self, start_time, current_time):
				return (current_time-start_time) > self.timeout

		def scrap_to_json(self):
				# call the __start_driver and override class member __driver to webdriver's instance
				self.__start_driver()
				starting_time = time.time()

				# navigate to URL
				self.__driver.get(self.URL)

				self.get_cookies()

				# only login if username is provided
				self.username is not None and Finder._Finder__login(self.__driver, self.username, self.password)
				Finder._Finder__accept_cookies(self.__driver)
				self.__layout = Finder._Finder__detect_ui(self.__driver)
				# sometimes we get popup that says "your request couldn't be processed", however
				# posts are loading in background if popup is closed, so call this method in case if it pops up.
				Utilities._Utilities__close_error_popup(self.__driver)
				# wait for post to load
				elements_have_loaded = Utilities._Utilities__wait_for_element_to_appear(
						self.__driver, self.__layout, self.timeout)
				# scroll down to bottom most
				Utilities._Utilities__scroll_down(self.__driver, self.__layout)
				self.__handle_popup(self.__layout)

				while len(self.__data_dict) < self.posts_count and elements_have_loaded:
						self.__handle_popup(self.__layout)
						# self.__find_elements(name)
						self.__find_elements()
						current_time = time.time()
						if self.__check_timeout(starting_time, current_time) is True:
								logger.setLevel(logging.INFO)
								logger.info('Timeout...')
								break
						Utilities._Utilities__scroll_down(
								self.__driver, self.__layout)  # scroll down
				# close the browser window after job is done.
				Utilities._Utilities__close_driver(self.__driver)
				# dict trimming, might happen that we find more posts than it was asked, so just trim it
				self.__data_dict = dict(list(self.__data_dict.items())[
																0:int(self.posts_count)])

				return json.dumps(self.__data_dict, ensure_ascii=False)

		def edit_language(self):
				# call the __start_driver and override class member __driver to webdriver's instance
				self.__start_driver()
				starting_time = time.time()
				# navigate to URL
				self.__driver.get('https://facebook.com/language')

				logger.info(f"PAGE TITLE: {self.__driver.title}")

				Finder._Finder__accept_cookies(self.__driver)
				self.__layout = Finder._Finder__detect_ui(self.__driver)
				# sometimes we get popup that says "your request couldn't be processed", however
				# posts are loading in background if popup is closed, so call this method in case if it pops up.
				Utilities._Utilities__close_error_popup(self.__driver)

				Utilities._Utilities__click_language_select(self.__driver)

				# close the browser window after job is done.
				Utilities._Utilities__close_driver(self.__driver)

				return {'status': True, 'message': 'Language Edited'}

		def __remove_duplicates(self, all_posts):
				"""takes a list of posts and removes duplicates from it and returns the list"""
				if len(self.__extracted_post) == 0:  # if self.__extracted_post is empty that means it is first extraction
						# if it does than just add all the elements from the lists to __extracted_post set()
						self.__extracted_post.update(all_posts)
						return all_posts  # return the all_posts without any changes as it is first time and no duplicate is present
				else:
						# if self.extracted posts have some element than compare it with all_posts's element and return a new list containing new element
						removed_duplicated = [
								post for post in all_posts if post not in self.__extracted_post]
						# after removing duplicates, add all those new element to extracted_posts, as it
						self.__extracted_post.update(all_posts)
						return removed_duplicated  # is set() it won't have duplicate elements

		def __close_after_retry(self):
				"""returns if class member retry is 0"""
				return self.retry <= 0

		def __no_post_found(self, all_posts):
				"""if all_posts were found to be length of 0"""
				if len(all_posts) == 0:
						# if length of posts is 0,decrement retry by 1
						self.retry -= 1

		def get_cookies(self):
				current_cookies = self.__driver.get_cookies()
				logger.setLevel(logging.INFO)
				logger.info(f"CURRENT COOKIES: {current_cookies}")

				if self.cookies:
						try:
							with open(self.cookies, 'r') as inputdata:
									cookies = json.load(inputdata)
									for cookie in cookies:
											if 'sameSite' in cookie:
													if cookie['sameSite'] == 'None':
															cookie['sameSite'] = 'Strict'
											self.__driver.add_cookie(cookie)
							self.__driver.refresh()
							logger.info(f"UPDATED COOKIES: {self.__driver.get_cookies()}")
						except Exception as e:
								logger.warning(e)
								pass
				time.sleep(15)

				return {'success': True, 'message': "COOKIES UPDATED"}

		def scrape_user_data(self):
				"""
				Performs the scraping process to retrieve general and profile page information.

				Returns:
						dict: A combined dictionary with general and profile page information, or None if extraction fails.
				"""
				html_content = RequestHandler._RequestHandler__fetch_html(self.URL)

				# Parse general information
				general_info_json = RequestHandler._RequestHandler__parse_json_from_html(
						html_content, "username_for_profile"
				)
				general_info = UserDataScraper._UserDataScraper__extract_general_info(general_info_json)

				# Parse profile information
				profile_info_json = RequestHandler._RequestHandler__parse_json_from_html(
						html_content, "profile_tile_items"
				)
				profile_info = UserDataScraper._UserDataScraper__extract_profile_info(profile_info_json)

				# Combine both into one dictionary
				if general_info and profile_info:
						combined_info = {**general_info, **profile_info}
						return combined_info
				elif general_info:
						return general_info
				elif profile_info:
						return profile_info
				else:
						return None

		def __find_elements(self):
				logger.setLevel(logging.DEBUG)
				"""find elements of posts and add them to data_dict"""
				all_posts = Finder._Finder__find_all_posts(
						self.__driver, self.__layout, self.isGroup)  # find all posts
				print("all_posts length: " + str(len(all_posts)))

				 # remove duplicates from the list
				all_posts = self.__remove_duplicates(
						all_posts) 

				# iterate over all the posts and find details from the same
				for post in all_posts:
						try:
								# find post ID from post
								status, post_url, link_element = Finder._Finder__find_status(
										post, self.__layout, self.isGroup)
								if post_url is None:
										print("no post_url, skipping LEL")
										continue

								# Split the URL on the '?' character, to detach the referer or uneeded query info
								parts = post_url.split('?')
								# The first part of the list is the URL up to the '?'
								post_url = parts[0]

								# finds name depending on if this facebook site is a page or group (we pass a post obj or a webDriver)
								name, user_url = Finder._Finder__find_name(post, self.__layout)
								if name is None:
									logger.exception("No name, skip POST")
									continue
								
								post_content = Finder._Finder__find_content(
										post, self.__driver, self.__layout)
								#print("comments: " + post_content)
								
								# NOTE below is  additional fields to scrape, all of which have not been thoroughly tested for groups
								if not self.isGroup:
										# find share from the post
										shares = Finder._Finder__find_share(post, self.__layout)
										# converting shares to number
										# e.g if 5k than it should be 5000
										shares = int(
												Scraping_utilities._Scraping_utilities__value_to_float(shares))
										# find all reactions
										reactions_all = Finder._Finder__find_reactions(post)
										# find all anchor tags in reactions_all list
										all_hrefs_in_react = Finder._Finder__find_reaction(self.__layout, reactions_all,) if type(
												reactions_all) != str else ""
										# if hrefs were found
										# all_hrefs contains elements like
										# ["5 comments","54 Likes"] and so on
										if type(all_hrefs_in_react) == list:
												l = [i.get_attribute("aria-label")
														for i in all_hrefs_in_react]
										else:
												l = []
										# extract that aria-label from all_hrefs_in_react list and than extract number from them seperately
										# if Like aria-label is in the list, than extract it and extract numbers from that text

										likes = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Нравится")
										# if Love aria-label is in the list, than extract it and extract numbers from that text
										loves = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Супер")
										# if Wow aria-label is in the list, than extract it and extract numbers from that text
										wow = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Ух ты")
										# if Care aria-label is in the list, than extract it and extract numbers from that text
										cares = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Мы вместе")
										# if Sad aria-label is in the list, than extract it and extract numbers from that text
										sad = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Сочувствую")
										# if Angry aria-label is in the list, than extract it and extract numbers from that text
										angry = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Возмутительно")
										# if Haha aria-label is in the list, than extract it and extract numbers from that text
										haha = Scraping_utilities._Scraping_utilities__find_reaction_by_text(
												l, "Ха-ха")

										# converting all reactions to numbers
										# e,g reactions may contain counts like "5k","5m", so converting them to actual number
										likes = Scraping_utilities._Scraping_utilities__value_to_float(
												likes)
										loves = Scraping_utilities._Scraping_utilities__value_to_float(
												loves)
										wow = Scraping_utilities._Scraping_utilities__value_to_float(
												wow)
										cares = Scraping_utilities._Scraping_utilities__value_to_float(
												cares)
										sad = Scraping_utilities._Scraping_utilities__value_to_float(
												sad)
										angry = Scraping_utilities._Scraping_utilities__value_to_float(
												angry)
										haha = Scraping_utilities._Scraping_utilities__value_to_float(
												haha)

										reactions = {"likes": int(likes), "loves": int(loves), "wow": int(wow), "cares": int(cares), "sad": int(sad),
																"angry":
																int(angry), "haha": int(haha)}

										# count number of total reactions
										total_reaction_count = Scraping_utilities._Scraping_utilities__count_reaction(
												reactions)

										comments = Finder._Finder__find_comments(post, self.__layout)
										comments = int(
												Scraping_utilities._Scraping_utilities__value_to_float(comments))
										

										# extract time
										posted_time = Finder._Finder__find_posted_time(
												post, self.__layout, link_element, self.__driver, self.isGroup)

										video, video_thumbnail = Finder._Finder__find_video_url(post, status)

								image = Finder._Finder__find_image_url(post, self.__layout)

								# post_url = "https://www.facebook.com/{}/posts/{}".format(self.page_or_group_name,status)

								self.__data_dict[status] = {
										"name": name,
										"user_url": user_url,
										"content": post_content,
										"images": image,
										"post_url": post_url,
										# NOTE only include the following fields if scraping a page, not tested for groups yet
										**({"shares": shares} if not self.isGroup else {}),
										**({"likes": int(likes)} if not self.isGroup else {}),
										**({"reactions": reactions} if not self.isGroup else {}),
										**({"reaction_count": total_reaction_count} if not self.isGroup else {}),
										**({"comments": comments} if not self.isGroup else {}),
										**({"posted_on": posted_time} if not self.isGroup else {}),
										**({"video": video} if not self.isGroup else {}),
										**({"video_thumbnail": video_thumbnail} if not self.isGroup else {}),
								}
						except Exception as ex:
								logger.exception(
										"Error at find_elements method : {}".format(ex))
