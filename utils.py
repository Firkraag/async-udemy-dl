#!/usr/bin/env python
# encoding: utf-8
import argparse
import asyncio
import logging
import os
from typing import Generator, Tuple, Optional

import requests

from constants import MY_COURSES_URL, HEADERS


def coroutine_retry(retry_times: int = 5, sleep: int = 1):
    """
    retry coroutine at most `retry_time` times when encountering exception
    :param retry_times:
    :param sleep:
    :return:
    """

    def wrap(func):
        async def wrap2(*args, **kwargs):
            for i in range(retry_times + 1):
                try:
                    return await func(*args, **kwargs)
                except:
                    logging.exception("")
                    if i == retry_times:
                        raise
                    await asyncio.sleep(sleep)

        return wrap2

    return wrap


Index = Start = Stop = int


def partition(start: int, stop: int, interval_size: int) \
        -> Generator[Tuple[Index, Start, Stop], None, None]:
    """
    partition range ranging from `start` to `stop` to intervals size of each is `size`,
    except the last interval.
    :param start:
    :param stop:
    :param interval_size:
    :return:
    """
    index = 0
    while start <= stop:
        yield index, start, min(start + interval_size - 1, stop)
        start += interval_size
        index += 1


def get_udemy_accss_token(cookies_filepath: str) -> str:
    """
    get access token from udemy cookies file
    :param cookies_filepath: udemy cookies file path
    :return:
    """
    with open(cookies_filepath) as cookie_file:
        cookies = cookie_file.read()
    cookies = [items.split("=", 1) for items in cookies.split(";")]
    cookies = {key.strip(): value.strip() for key, value in cookies}
    return cookies['access_token']


def get_output_directory(output: Optional[str]) -> str:
    """
    If output is empty or None, return current directory,
    otherwise use output, then expand ~ and ~user and convert it to absolute path.
    :param output:
    :return:
    """
    if not output:
        return os.getcwd()
    return os.path.realpath(os.path.expanduser(output))


UdemyInfo = dict


def get_udemy_course_info_by_course_name(course_name: str) -> Optional[UdemyInfo]:
    """
    :param course_name:
    :return:
    """
    response = requests.get(MY_COURSES_URL, headers=HEADERS)
    udemy_course_infos = response.json()['results']
    for udemy_course_info in udemy_course_infos:
        if udemy_course_info['published_title'] == course_name:
            return udemy_course_info
    return None


def argment_processing():
    """
    command line argument processing
    :return:
    """
    description = 'A cross-platform python based utility to ' \
                  'download courses from udemy for personal offline use.'
    parser = argparse.ArgumentParser(description=description, conflict_handler='resolve')
    parser.add_argument('course_name', help="Udemy course.", type=str)
    general = parser.add_argument_group("General")
    general.add_argument('-h', '--help', action='help', help="Shows the help.")

    authentication = parser.add_argument_group("Authentication")
    authentication.add_argument('-k', '--cookies-file', dest='cookies', type=str,
                                help="Cookies file to authenticate with.", required=True)

    advance = parser.add_argument_group("Advance")
    advance.add_argument('-o', '--output', dest='output', type=str,
                         help="Download to specific directory. "
                              "If not specified, download to current directory")
    advance.add_argument('-c', '--chapter', dest='chapter', type=int,
                         help="Download specific chapter from course.")
    advance.add_argument('-l', '--lecture', dest='lecture', type=int,
                         help="Download specific lecture from chapter(s).")
    advance.add_argument('--chapter-start', dest='chapter_start', type=int,
                         help="Download from specific position within course.")
    advance.add_argument('--chapter-end', dest='chapter_end', type=int,
                         help="Download till specific position within course.")
    advance.add_argument('--lecture-start', dest='lecture_start', type=int,
                         help="Download from specific position within chapter(s).")
    advance.add_argument('--lecture-end', dest='lecture_end', type=int,
                         help="Download till specific position within chapter(s).")
    return parser.parse_args()
