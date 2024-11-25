#!/usr/bin/env python3
import datetime
import logging
import re
import sys
import time
import urllib.request

from typing import Optional, Dict
from .request_handler import RequestHandler

logger = logging.getLogger(__name__)
format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)

class UserDataScraper:

    @staticmethod
    def __extract_general_info(self, json_data: dict) -> Dict[str, Optional[str]]:
        """
        Extracts general page information (name, URL, profile picture, likes, followers).

        Args:
            json_data (dict): The parsed JSON data.

        Returns:
            dict: A dictionary with general page information.
        """
        general_info = {
            "page_name": None,
            "page_url": None,
            "profile_pic": None,
            "page_likes": None,
            "page_followers": None,
        }

        try:
            requires = json_data.get("require", [])
            if not requires:
                raise ValueError("Missing 'require' key in JSON data.")
            requires = requires[0][3][0].get("__bbox", {}).get("require", [])

            for require in requires:
                if "RelayPrefetchedStreamCache" in require:
                    result = require[3][1].get("__bbox", {}).get("result", {})
                    user = (
                        result.get("data", {})
                        .get("user", {})
                        .get("profile_header_renderer", {})
                        .get("user", {})
                    )

                    general_info["page_name"] = user.get("name")
                    general_info["page_url"] = user.get("url")
                    general_info["profile_pic"] = (
                        user.get("profilePicLarge", {}).get("uri")
                        or user.get("profilePicMedium", {}).get("uri")
                        or user.get("profilePicSmall", {}).get("uri")
                    )

                    profile_social_contents = user.get(
                        "profile_social_context", {}
                    ).get("content", [])
                    for content in profile_social_contents:
                        uri = content.get("uri", "")
                        text = content.get("text", {}).get("text")
                        if "friends_likes" in uri and not general_info["page_likes"]:
                            general_info["page_likes"] = text
                        elif "followers" in uri and not general_info["page_followers"]:
                            general_info["page_followers"] = text
                        if (
                            general_info["page_likes"]
                            and general_info["page_followers"]
                        ):
                            break
            return general_info
        except (IndexError, KeyError, TypeError, ValueError) as e:
            print(f"Error extracting general page information: {e}")
            return general_info

    @staticmethod
    def __extract_profile_info(self, json_data: dict) -> Dict[str, Optional[str]]:
        """
        Extracts detailed profile information from the parsed JSON data.

        Args:
            json_data (dict): The parsed JSON data.

        Returns:
            dict: A dictionary with detailed profile information.
        """
        matching_types = {
            "INTRO_CARD_INFLUENCER_CATEGORY": "page_category",
            "INTRO_CARD_ADDRESS": "page_address",
            "INTRO_CARD_PROFILE_PHONE": "page_phone",
            "INTRO_CARD_PROFILE_EMAIL": "page_email",
            "INTRO_CARD_WEBSITE": "page_website",
            "INTRO_CARD_BUSINESS_HOURS": "page_business_hours",
            "INTRO_CARD_BUSINESS_PRICE": "page_business_price",
            "INTRO_CARD_RATING": "page_rating",
            "INTRO_CARD_BUSINESS_SERVICES": "page_services",
            "INTRO_CARD_OTHER_ACCOUNT": "page_social_accounts",
        }

        profile_info = {value: None for value in matching_types.values()}

        try:
            requires = json_data.get("require", [])
            if not requires:
                raise ValueError("Missing 'require' key in JSON data.")
            requires = requires[0][3][0].get("__bbox", {}).get("require", [])

            for require in requires:
                if "RelayPrefetchedStreamCache" in require:
                    result = require[3][1].get("__bbox", {}).get("result", {})
                    profile_tile_sections = (
                        result.get("data", {})
                        .get("profile_tile_sections", {})
                        .get("edges", [])
                    )

                    for section in profile_tile_sections:
                        nodes = (
                            section.get("node", {})
                            .get("profile_tile_views", {})
                            .get("nodes", [])
                        )
                        for node in nodes:
                            view_style_renderer = node.get("view_style_renderer")
                            if not view_style_renderer:
                                continue
                            profile_tile_items = (
                                view_style_renderer.get("view", {})
                                .get("profile_tile_items", {})
                                .get("nodes", [])
                            )
                            for item in profile_tile_items:
                                timeline_context_item = item.get("node", {}).get(
                                    "timeline_context_item", {}
                                )
                                item_type = timeline_context_item.get(
                                    "timeline_context_list_item_type"
                                )
                                if item_type in matching_types:
                                    text = (
                                        timeline_context_item.get("renderer", {})
                                        .get("context_item", {})
                                        .get("title", {})
                                        .get("text")
                                    )
                                    if text:
                                        key = matching_types[item_type]
                                        profile_info[key] = text
            return profile_info
        except (IndexError, KeyError, TypeError, ValueError) as e:
            print(f"Error extracting profile information: {e}")
            return profile_info