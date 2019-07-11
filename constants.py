#!/usr/bin/env python
# encoding: utf-8
CHUNKSIZE = 1024 * 512
PART_NUMBER = 10
MY_COURSES_URL = "https://www.udemy.com/api-2.0/users/me/subscribed-courses?fields[course]="
"id,url,published_title&ordering=-access_time&page=1&page_size=10000"
COURSE_URL = 'https://www.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items?'
'fields[asset]=results,external_url,time_estimation,download_urls,slide_urls,filename,asset_type,'
'captions,stream_urls,body&fields[chapter]=object_index,title,sort_order&fields[lecture]=id,title,'
'object_index,asset,supplementary_assets,view_html&page_size=10000'
HEADERS = {
    'Host': 'www.udemy.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    'Referer': 'https://www.udemy.com/join/login-popup/',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}
