#!/usr/bin/env python
# encoding: utf-8
import asyncio
import os
from datetime import datetime
from functools import reduce

import aiohttp
import requests

CHUNKSIZE = 1024 * 512
MY_COURSES_URL = "https://www.udemy.com/api-2.0/users/me/subscribed-courses?fields[course]=id,url,published_title&ordering=-access_time&page=1&page_size=10000"
COURSE_URL = 'https://www.udemy.com/api-2.0/courses/{course_id}/cached-subscriber-curriculum-items?fields[asset]=results,external_url,time_estimation,download_urls,slide_urls,filename,asset_type,captions,stream_urls,body&fields[chapter]=object_index,title,sort_order&fields[lecture]=id,title,object_index,asset,supplementary_assets,view_html&page_size=10000'
HEADERS = {
    'Host': 'www.udemy.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    'Referer': 'https://www.udemy.com/join/login-popup/',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
    # 'X-Requested-With'  : 'XMLHttpRequest',
    # This header is taken from https://github.com/FaisalUmair/udemy-downloader-gui thanks to @FaisalUmair for quick help.
    # "Authorization": "Basic YWQxMmVjYTljYmUxN2FmYWM2MjU5ZmU1ZDk4NDcxYTY6YTdjNjMwNjQ2MzA4ODI0YjIzMDFmZGI2MGVjZmQ4YTA5NDdlODJkNQ=="
}
ROOT_DIRECTORY = 'udemy_courses'
PART_NUMBER = 10


class UdemyCourse(object):
    def __init__(self, id, url, published_title):
        self.id = id
        self.url = url
        self.published_title = published_title
        self.chapters = []
        self.directory = os.path.join(ROOT_DIRECTORY, published_title)

        try:
            os.mkdir(self.directory)
        except:
            pass

        self.get_course_detail()

    def get_course_detail(self):
        response = requests.get(COURSE_URL.format(course_id=self.id), headers=HEADERS)
        results = response.json()
        resources = results['results']
        chapters_and_lectures = []

        def foo(value, element):
            class_ = element['_class']
            if class_ == 'chapter':
                l = [element]
                chapters_and_lectures.append(l)
            elif class_ == 'lecture':
                chapters_and_lectures[-1].append(element)
            return element

        chapters_and_lectures.append([resources[0]])
        reduce(foo, resources[1:], resources[0])
        for chapter_and_lectures in chapters_and_lectures:
            chapter = chapter_and_lectures[0]
            lectures = chapter_and_lectures[1:]
            udemy_chapter = UdemyChapter(chapter['id'], chapter['sort_order'], chapter['title'],
                                         chapter['object_index'], self, lectures)
            self.chapters.append(udemy_chapter)

    async def download(self, session: aiohttp.ClientSession, chapter_start=None, chapter_end=None,
                       lecture_start=None,
                       lecture_end=None):
        if chapter_start is None:
            chapter_start = 0
        else:
            chapter_start = chapter_start - 1

        if chapter_end is None:
            chapter_end = len(self.chapters) - 1
        else:
            chapter_end = chapter_end - 1

        await asyncio.gather(*(chapter.download(session, lecture_start, lecture_end) for chapter in
                               self.chapters[chapter_start:chapter_end + 1]))


class UdemyChapter(object):
    def __init__(self, id, sort_order, title, object_index, course: UdemyCourse, lectures):
        self.id = id
        self.sort_order = sort_order
        self.title = title
        self.chapter_index = f'{object_index:02d}'
        self.lectures = []
        self.course = course
        self.directory = os.path.join(course.directory, self.chapter_index + " " + title)

        try:
            os.mkdir(self.directory)
        except:
            pass
        for lecture in lectures:
            udemy_lecture = UdemyLecture(lecture['id'], lecture['title'], lecture['asset'],
                                         lecture['object_index'], lecture['supplementary_assets'],
                                         self)
            self.lectures.append(udemy_lecture)

    async def download(self, session: aiohttp.ClientSession, lecture_start=None, lecture_end=None):
        if lecture_start is None:
            lecture_start = 0
        else:
            lecture_start -= 1

        if lecture_end is None:
            lecture_end = len(self.lectures) - 1
        else:
            lecture_end -= 1

        # for lecture in self.lectures[lecture_start:lecture_end + 1]:
        #     lecture.download()
        await asyncio.gather(
            *(lecture.download(session) for lecture in
              self.lectures[lecture_start:lecture_end + 1]))


class UdemyLecture(object):
    def __init__(self, id, title, asset, object_index, supplementary_assets, chapter: UdemyChapter):
        self.id = id
        self.title = title
        self.lecture_index = f'{object_index:03d}'
        self.supplementary_assets = supplementary_assets
        self.chapter = chapter
        self.directory = chapter.directory
        self.asset = None
        self.supplementary_assets = []
        asset_type = asset['asset_type']
        if asset_type == 'Video':
            self.asset = UdemyAssetVideo(asset['time_estimation'], asset['captions'],
                                         asset['filename'], asset['stream_urls'], asset['id'],
                                         asset['body'], asset['slide_urls'], asset['download_urls'],
                                         asset['external_url'], self)
        elif asset_type == 'Article':
            self.asset = UdemyAssetArticle(asset['id'], asset['body'], asset['time_estimation'],
                                           self)

        for supplementary_asset in supplementary_assets:
            asset_type = supplementary_asset['asset_type']
            if asset_type == 'ExternalLink':
                self.supplementary_assets.append(
                    UdemyAssetEternalLink(supplementary_asset['time_estimation'],
                                          supplementary_asset['id'],
                                          supplementary_asset['filename'],
                                          supplementary_asset['external_url'], self))

    async def download(self, session):
        if self.asset:
            await self.asset.download(session)

        for supplementary_asset in self.supplementary_assets:
            supplementary_asset.download()


class UdemyAssetEternalLink(object):
    def __init__(self, time_estimation, id, filename, external_url, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        self.id = id
        self.filename = filename
        self.external_url = external_url
        self.lecture = lecture
        self.directory = lecture.directory

    def download(self):
        filename = self.lecture.lecture_index + " " + self.filename + '.txt'
        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(self.external_url)


class UdemyAssetVideo(object):
    def __init__(self, time_estimation, captions, filename, stream_urls, id, body, slide_urls,
                 download_urls, external_urls, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        # self.captions = captions
        self.filename = filename
        # self.stream_urls = stream_urls
        self.id = id
        self.body = body
        self.slide_urls = slide_urls
        self.download_urls = download_urls
        self.external_urls = external_urls
        self.lecture = lecture
        self.directory = lecture.directory
        self.captions = []

        for caption in captions:
            self.captions.append(UdemyCaption(caption['id'], caption['title'], caption['created'],
                                              caption['file_name'], caption['status'],
                                              caption['url'], caption['source'],
                                              caption['locale_id'], caption['video_label'],
                                              caption['asset_id'], self))
        self.streams = []
        for stream in stream_urls['Video']:
            self.streams.append(UdemyStream(stream['type'], stream['label'], stream['file'], self))

    async def download(self, session):
        for caption in self.captions:
            caption.download()

        stream = max([stream for stream in self.streams if 'x-mpegURL' not in stream.type],
                     key=lambda stream: int(stream.label))

        await stream.download(session)


class UdemyAssetArticle(object):
    def __init__(self, id, body, time_estimation, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        self.id = id
        self.body = body
        self.lecture = lecture
        self.title = self.lecture.lecture_index + ' ' + self.lecture.title
        self.file_name = self.title + '.html'
        self.directory = self.lecture.directory

    async def download(self, session):
        data = '''
                <html>
                <head>
                <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
                <title>%s</title>
                </head>
                <body>
                <div class="container">
                <div class="row">
                <div class="col-md-10 col-md-offset-1">
                    <p class="lead">%s</p>
                </div>
                </div>
                </div>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
                </body>
                </html>
                ''' % (self.title, self.body)
        with open(os.path.join(self.directory, self.file_name), 'w') as f:
            f.write(data)


class UdemyStream(object):
    def __init__(self, type, label, file, asset):
        self.type = type
        self.label = label
        self.file = file
        self.asset = asset
        self.directory = asset.directory
        format = self.type.split('/')[-1]
        self.file_path = os.path.join(self.directory,
                                      asset.lecture.lecture_index + " " + asset.lecture.title + '.' + format)
        self.temp_file_path = os.path.join(self.directory,
                                           asset.lecture.lecture_index + " " + asset.lecture.title + '.' + format + '.part')

    async def download(self, session, retry=5):
        try:
            if os.path.exists(self.file_path):
                return
            headers = {'User-Agent': HEADERS.get('User-Agent')}
            async with session.get(self.file, headers=headers) as resp:
                content_length = resp.content_length
            interval = range(0, content_length, CHUNKSIZE * PART_NUMBER)
            ranges = [
                (i, part_start, min(part_start + CHUNKSIZE * PART_NUMBER - 1, content_length - 1))
                for i, part_start in enumerate(interval)]
            for i, start, end in ranges:
                await self.download_part(i, start, end, session)

            with open(self.file_path, 'ab') as f:
                for part_temp_path in [self.temp_file_path + str(j + 1) for j in range(i + 1)]:
                    with open(part_temp_path, 'rb') as part_f:
                        f.write(part_f.read())
            for part_temp_path in [self.temp_file_path + str(j + 1) for j in range(i + 1)]:
                os.remove(part_temp_path)
        except Exception as e:
            print(f"get stream info error, exception = {e}")
            if retry:
                await asyncio.sleep(3)
                await self.download(session)
            else:
                raise e

    async def download_part(self, index, start, end, session):
        if os.path.exists(self.temp_file_path + str(index + 1)):
            return
        # headers = {'User-Agent': HEADERS.get('User-Agent')}
        interval = range(start, end + 1, CHUNKSIZE)
        ranges = [(i, part_start, min(part_start + CHUNKSIZE - 1, end)) for i, part_start in
                  enumerate(interval)]
        await asyncio.gather(*[self._download_part(index, i, part_start, part_end, session) for
                               i, part_start, part_end in ranges])
        part_temp_path = self.temp_file_path + str(index + 1)
        with open(part_temp_path, 'ab') as f:
            for part_part_temp_path in [self.temp_file_path + str(index + 1) + str(index2 + 1) for
                                        index2 in range(len(interval))]:
                with open(part_part_temp_path, 'rb') as part_f:
                    f.write(part_f.read())
        for part_part_temp_path in [self.temp_file_path + str(index + 1) + str(index2 + 1) for
                                    index2 in range(len(interval))]:
            os.remove(part_part_temp_path)
        # for part_temp_path in [self.temp_file_path + str(i + 1) for i in range(PART_NUMBER)]:
        #     os.remove(part_temp_path)
        # with open(part_temp_path, 'ab') as f:
        #     async with session.get(self.file, headers=headers) as resp:
        #         while True:
        #             count = 5
        #             while count > 0:
        #                 try:
        #                     chunk = await resp.content.read(CHUNKSIZE)
        #                 except Exception as e:
        #                     print(f"response read exception {e}")
        #                     # await asyncio.sleep(3)
        #                     count -= 1
        #                     if count == 0:
        #                         raise e
        #                 else:
        #                     break
        #             if not chunk:
        #                 break
        #             print(f"{self.asset.lecture.title} read {len(chunk)} bytes")
        #             f.write(chunk)
        #             f.flush()

    async def _download_part(self, index1, index2, start, end, session, retry=5):
        part_temp_path = self.temp_file_path + str(index1 + 1) + str(index2 + 1)
        headers = {'User-Agent': HEADERS.get('User-Agent')}
        if os.path.exists(part_temp_path):
            offset = os.stat(part_temp_path).st_size
            if offset >= (end - start + 1):
                return
            headers['Range'] = f"bytes={start + offset}-{end}"
        else:
            headers['Range'] = f'bytes={start}-{end}'
        print(f"part{index1}{index2} {start} - {end}")
        with open(part_temp_path, 'ab') as f:
            try:
                async with session.get(self.file, headers=headers) as resp:
                    while True:
                        chunk = await resp.content.read(CHUNKSIZE)
                        if not chunk:
                            break
                        print(f"{self.asset.lecture.title} read {len(chunk)} bytes")
                        f.write(chunk)
                        # f.flush()
            except Exception as e:
                print(f"response read exception {e}")
                if retry:
                    await asyncio.sleep(3)
                    await self._download_part(index1, index2, start, end, session, retry - 1)
                else:
                    raise e

        print(f"{self.asset.lecture.title} part{index1}{index2} reads {os.stat(
            part_temp_path).st_size} bytes ")


class UdemyCaption(object):
    def __init__(self, id, title, created, file_name, status, url, source, locale_id, video_label,
                 asset_id, asset):
        self.id = id
        self.title = title
        self.created = created
        self.file_name = file_name
        self.status = status
        self.source = source
        self.locale_id = locale_id
        self.video_label = video_label
        self.asset_id = asset_id
        self.url = url
        self.asset = asset
        self.directory = asset.directory
        self.filename = self.asset.lecture.lecture_index + ' ' + self.asset.lecture.title + '-' + \
                        locale_id.split('_')[0] + '.srt'

    def download(self):
        file_path = os.path.join(self.directory, self.filename)
        if os.path.exists(file_path):
            return
        headers = {'User-Agent': HEADERS.get('User-Agent')}
        with open(file_path, 'wb') as f:

            try:
                response = requests.get(self.url, headers=headers)
            except Exception as e:
                e
            else:
                f.write(response.content)


async def main(course_name, chapter_start=None, chapter_end=None, lecture_start=None,
               lecture_end=None):
    # logging.basicConfig('')
    now = datetime.now()
    print(f"download starts at {now.strftime('%H:%M:%S')}")
    with open('cookies.txt') as f:

        s = f.read()
        cookies = [items.split("=", 1) for items in s.split(";")]
        cookies = {key.strip(): value.strip() for key, value in cookies}
        access_token = cookies['access_token']
        HEADERS.update({
            'Authorization': f'Bearer {access_token}',
            'X-Udemy-Authorization': f'Bearer {access_token}',
        })
        response = requests.get(MY_COURSES_URL, headers=HEADERS)
        courses = response.json()['results']
        for course in courses:
            if course['published_title'] == course_name:
                udemy_course = UdemyCourse(course['id'], course['url'], course['published_title'])
                async with aiohttp.ClientSession() as session:
                    await udemy_course.download(session, chapter_start, chapter_end, lecture_start,
                                                lecture_end)
    print(f"download ends at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == '__main__':
    asyncio.run(main('try-django-1-10'))
