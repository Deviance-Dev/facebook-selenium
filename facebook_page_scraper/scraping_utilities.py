#!/usr/bin/env python3
import logging
import re
from datetime import datetime
from datetime import datetime as dt
from datetime import timedelta
import dateparser

from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)
format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)

class Scraping_utilities:
    @staticmethod
    def __extract_numbers(string):
        """expects string and returns numbers from them as integer type,
        e.g => input = '54454 comment', than output => 54454
        """
        try:
            # return string.split(" ")[0]
            return re.findall("\d+", string)[0]
        except IndexError:
            return 0

    @staticmethod
    def __exists_in_list(li, word):
        """expects list and a element, returns all the occurence of element in the list.
        e.g input => li = ['sajid','sajid','sajid','d','s'] with given word = 'sajid',
        output => ['sajid','sajid','sajid'] """
        return [substring for substring in li if word in substring]

    @staticmethod
    def __convert_time(unix_timestamp):
        try:
            return dt.utcfromtimestamp(float(unix_timestamp)).isoformat()
        except Exception as ex:
            logger.exception('Error at convert_time : {}'.format(ex))

    @staticmethod
    def __extract_content(content):
        """returns the text content of selenium element, else if content is string than returns a empty string"""
        if type(content) is not str:
            all_para = content.find_elements(By.TAG_NAME, "p")
            paragraph = ''
            for para in all_para:
                paragraph += para.get_attribute("textContent")
                content = paragraph
        else:
            content = ""
        return content

    @staticmethod
    def __count_reaction(dictionary):
        """expects a dictionary and returns sum of all values of dictionary.
        e.g =>
        input dictionary = {"s":1,"d":34},
        output=> 35"""
        return sum(dictionary.values())

    @staticmethod
    def __extract_id_from_link(link):
        """expects the post's URL as a argument, and extracts out post_id from that URL"""
        try:
            status = "NA"
            # if url pattern container "/posts"
            if "posts/" in link:
                status = link.split('/')[5].split('?')[0]
            # if url pattern container "/photos"
            elif "photos/" in link:
                status = link.split("/")[-2]
            # if url pattern container "/videos"
            if "/videos/" in link:
                status = link.split("/")[5]
            elif "/reel/" in link:
                status = link.split("/")[4]
            elif "/events/" in link:
                status = link.split("/")[4]
            elif "fbid=" in link:
                status = link.split("=")[1].split("&")[0]
            elif "group" in link:
                status = link.split("/")[6]
            return status
        except IndexError:
            pass
        except Exception as ex:
            logger.exception(
                'Error at extract_id_from_link : {}'.format(ex))

    @staticmethod
    def __value_to_float(x):
        try:
            x = float(x)
            return x
        except:
            pass
        x = x.lower()
        if 'k' in x:
            if len(x) > 1:
                return float(x.replace('k', '')) * 1000
            return 1000
        if 'm' in x:
            if len(x) > 1:
                return float(x.replace('m', '')) * 1000000
            return 1000000
        if 'm' in x:
            return float(x.replace('m', '')) * 1000000000
        return 0

    @staticmethod
    def __find_reaction_by_text(l, string):
        reaction = [substring for substring in l if string in substring]
        if len(reaction) == 0:
            return '0'
        reaction = re.findall(
            r"(\d+(?:\.\d+)?)([MmBbKk])?", reaction[0])
        if len(reaction) > 0:
            return ''.join(reaction[0]) #list of tuple, return first tuple's first result
        return '0'

    @staticmethod
    def __convert_to_iso(t):
        past_date = dateparser.parse(t, settings={'TIMEZONE': 'Asia/Tashkent'}).isoformat()
        if 'ч' in t.lower() or "hr" in t.lower() or "hrs" in t.lower():
            past_date = dateparser.parse(t, settings={'TIMEZONE': 'Asia/Tashkent'}).isoformat()

        if 'м' in t.lower() or "мин" in t.lower() or "mins" in t.lower():
            past_date = dateparser.parse(t, settings={'TIMEZONE': 'Asia/Tashkent'}).isoformat()

        if 'с' in t.lower():
            past_date = dateparser.parse(t, settings={'TIMEZONE': 'Asia/Tashkent'}).isoformat()

        if 'д' in t.lower() or "дн" in t.lower():
            past_date = dateparser.parse(t, settings={'TIMEZONE': 'Asia/Tashkent'}).isoformat()
        # print(f"time is : {t}")
        return past_date