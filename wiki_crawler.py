#!/usr/bin/env python

"""Script to crawl a dokuwiki."""

import requests
import logging
import sys
from lxml import html
from pathlib import Path
from datetime import datetime

__author__ = "Karl-Philipp Kortmann"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Karl-Philipp Kortmann"
__email__ = "philipp.kortmann@imes.uni-hannover.de"
__status__ = "stable"

### User Parameters: ONLY MODIFY THIS PART
# index page url
url_index = 'https://wiki.projekt.uni-hannover.de/imes-gruppe-medizintechnik/start?do=index'
# url until top level domain (e.g.: 'https://wiki.projekt.uni-hannover.de')
url_base = 'https://wiki.projekt.uni-hannover.de'
# your local download path
download_path = 'C:/Users/Kortmann/Downloads/test'
# your E-Mail for user login at wiki.projekt.uni-hannover.de (if None, E-Mail will be inquired while running)
user = None


### HTML indicator strings: Don't modify these unless dokuwiki's structure/version changes
str_recognize_index_page = 'alle vorhandenen Seiten'  # string in html code indicating a index page
str_index_start = '<div id="index__tree"'  # string in html code indicating the start of relevant (anchor) content
str_index_end = '<!-- wikipage stop -->'  # string in html code indicating the end of relevant (anchor) content


### CRAWLER SCRIPT
# start logging
logging_path = download_path + '/' + datetime.today().strftime('%Y%m%d_%H%M%S') + '_crawling.log'
logging.basicConfig(
    filename=logging_path,
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

# get credentials
print('Enter your credentials: ')
if user is None or not user:
    user = input('email: ')
else:
    print('email: ' + user)
pw = input('password: ')
payload = {'u': user, 'p': pw}

# get first link from index page
try:
    with requests.Session() as s:
        p = s.post(url_index, data=payload)
        print(p.content)
        # split html
        relevant_html_str = str(p.content).split(str_index_start)[1].split(str_index_end)[0]
        html_str = html.fromstring(relevant_html_str)
        print(html_str)
        active_link_list = html_str.xpath('//a/@href')
    active_link = active_link_list[0]
    full_active_link = url_base + active_link
    last_full_active_link = full_active_link
    logging.info('First link: ' + full_active_link)
    is_ready = False
except Exception as e:
    logging.warning(e)
    logging.info('Nothing to do here.')
    is_ready = True
    
# start depth-first search
while(not is_ready):
    # try downloading link
    with requests.Session() as s:
        p = s.post(full_active_link, data=payload)
        if str_recognize_index_page in str(p.content):
            # if result is not wiki page but another (sub-)index page
            logging.info('Nothing to download in: ' + full_active_link)
        else:
            # if result is wiki page
            # get markup content
            p = s.post(full_active_link + '?do=export_raw', data=payload)
            # create path if not exists
            cutted_link = active_link[:active_link.rfind('/')]
            dir_path = download_path + cutted_link
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            filepath = download_path + active_link + '.txt'
            # write text file
            open(filepath, 'wb').write(p.content)
            logging.info('Downloaded page to: ' + filepath)
            # set next full active link to last active link (which should be index url again)
            full_active_link = last_full_active_link
    
    # get next link from index page
    try:
        with requests.Session() as s:
            p = s.post(full_active_link, data=payload)
            # split html
            relevant_html_str = str(p.content).split(str_index_start)[1].split(str_index_end)[0]
            html_str = html.fromstring(relevant_html_str)
            active_link_list = html_str.xpath('//a/@href')
            active_link = active_link_list[active_link_list.index(active_link) + 1]
            last_full_active_link = full_active_link
            full_active_link = url_base + active_link
            logging.info('Next link to investigate: ' + full_active_link)
    except Exception as e:
        logging.warning(e)
        logging.info('Nothing more to do here.')
        is_ready = True
