#!/usr/bin/env python
# encoding: utf-8
import argparse
import asyncio
import logging
import os
import sys
from typing import Optional, List, Union, Generator, Tuple

import aiohttp
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
# __version__ = 0.3
Index = Start = Stop = int
Url = FilePath = str
AssetInfo = LectureInfo = dict
StreamInfoList = SupplementaryAssetInfoList = LectureInfoList = List[dict]

CHUNKSIZE = 1024 * 512
PART_NUMBER = 10
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
}


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
    print(udemy_course_infos)
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


class UdemyCourse:
    def __init__(self, id_: int, url: Url, published_title: str, output_directory: FilePath):
        self.id_ = id_
        self.url = url
        self.published_title = published_title
        self.chapters = []
        self.directory = os.path.join(output_directory, published_title)

        try:
            os.mkdir(self.directory)
        except FileExistsError:
            pass

        self.fill_course_chapters_and_lectures()

    def fill_course_chapters_and_lectures(self) -> None:
        """
        Get udemy course chapters info and store them at self.chapters.
        :return:
        """
        response = requests.get(COURSE_URL.format(course_id=self.id_), headers=HEADERS)
        results = response.json()
        # courses chapters and lectures info
        resources = results['results']
        # the first element of each element is chapter info,
        # and other elements of each element are lectures info,
        # like this: [[chapter1, lecture1, lecture2], [chapter2, lecture3]]
        chapters_and_lectures = []
        for chapter_or_lecture in resources:
            class_ = chapter_or_lecture['_class']
            if class_ == 'chapter':
                chapters_and_lectures.append([chapter_or_lecture])
            elif class_ == 'lecture':
                chapters_and_lectures[-1].append(chapter_or_lecture)
        for chapter_and_lectures in chapters_and_lectures:
            chapter = chapter_and_lectures[0]
            lectures = chapter_and_lectures[1:]
            print(chapter)
            udemy_chapter = UdemyChapter(chapter['id'], chapter['sort_order'], chapter['title'],
                                         chapter['object_index'], self, lectures)
            self.chapters.append(udemy_chapter)

    async def download(self, session: aiohttp.ClientSession, chapter: Optional[int] = None,
                       lecture: Optional[int] = None, chapter_start: Optional[int] = None,
                       chapter_end: Optional[int] = None, lecture_start: Optional[int] = None,
                       lecture_end: Optional[int] = None, ) -> None:
        logging.info(f"start downloading course {self.published_title}")
        if chapter is not None:
            chapter_start = chapter - 1
        elif chapter_start is None:
            chapter_start = 0
        else:
            chapter_start = chapter_start - 1

        if chapter is not None:
            chapter_end = chapter - 1
        elif chapter_end is None:
            chapter_end = len(self.chapters) - 1
        else:
            chapter_end = chapter_end - 1

        await asyncio.gather(
            *(chapter.download(session, lecture, lecture_start, lecture_end) for chapter in
              self.chapters[chapter_start:chapter_end + 1]))
        logging.info(f"end downloading course {self.published_title}")


class UdemyChapter:
    def __init__(self, id_: int, sort_order, title: str, object_index, course: UdemyCourse,
                 lectures: LectureInfoList):
        self.id_ = id_
        self.sort_order = sort_order
        self.title = title
        self.chapter_index = f'{object_index:02d}'
        self.lectures: List[UdemyLecture] = []
        self.course = course
        self.directory = os.path.join(course.directory, self.chapter_index + " " + title)

        try:
            os.mkdir(self.directory)
        except FileExistsError:
            pass
        for lecture in lectures:
            udemy_lecture = UdemyLecture(lecture['id'], lecture['title'], lecture['asset'],
                                         lecture['object_index'], lecture['supplementary_assets'],
                                         self)
            self.lectures.append(udemy_lecture)

    async def download(self, session: aiohttp.ClientSession, lecture: Optional[int] = None,
                       lecture_start: Optional[int] = None, lecture_end: Optional[int] = None):
        logging.info(f"start downloading chapter {self.title}")
        if lecture is not None:
            lecture_start = lecture - 1
        elif lecture_start is None:
            lecture_start = 0
        else:
            lecture_start -= 1

        if lecture is not None:
            lecture_end = lecture - 1
        elif lecture_end is None:
            lecture_end = len(self.lectures) - 1
        else:
            lecture_end -= 1

        await asyncio.gather(
            *(lecture.download(session) for lecture in
              self.lectures[lecture_start:lecture_end + 1]))
        logging.info(f"end downloading chapter {self.title}")


class UdemyLecture:
    def __init__(self, id_, title, asset: AssetInfo, object_index,
                 supplementary_assets: SupplementaryAssetInfoList, chapter: UdemyChapter):
        self.id_ = id_
        self.title = title
        self.lecture_index = f'{object_index:03d}'
        self.supplementary_assets = supplementary_assets
        self.chapter = chapter
        self.directory = chapter.directory
        self.asset: Optional[Union[UdemyAssetVideo, UdemyAssetArticle]] = None
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

    async def download(self, session: aiohttp.ClientSession):
        if self.asset:
            await self.asset.download(session)

        for supplementary_asset in self.supplementary_assets:
            supplementary_asset.download()


class UdemyAssetEternalLink:
    def __init__(self, time_estimation, id_, filename, external_url: Url, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        self.id_ = id_
        self.filename = filename
        self.external_url = external_url
        self.lecture = lecture
        self.directory = lecture.directory

    def download(self):
        filename = self.lecture.lecture_index + " " + self.filename + '.txt'
        with open(os.path.join(self.directory, filename), 'w') as f:
            f.write(self.external_url)


class UdemyAssetVideo:
    def __init__(self, time_estimation, captions, filename, streams: dict, id_, body, slide_urls,
                 download_urls, external_urls, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        # self.captions = captions
        self.filename = filename
        # self.stream_urls = stream_urls
        self.id_ = id_
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
        for stream in streams['Video']:
            self.streams.append(UdemyStream(stream['type'], stream['label'], stream['file'], self))

    async def download(self, session: aiohttp.ClientSession):
        for caption in self.captions:
            caption.download()
        # download video with max resolution
        stream = max([stream for stream in self.streams if 'x-mpegURL' not in stream.type_],
                     key=lambda stream_: int(stream_.label))

        await stream.download(session)


class UdemyAssetArticle:
    def __init__(self, id_, body, time_estimation, lecture: UdemyLecture):
        self.time_estimation = time_estimation
        self.id_ = id_
        self.body = body
        self.lecture = lecture
        self.title = self.lecture.lecture_index + ' ' + self.lecture.title
        self.file_name = self.title + '.html'
        self.directory = self.lecture.directory

    async def download(self, session):
        data = '''
                <html>
                <head>
                <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" 
                rel="stylesheet" 
                integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" 
                crossorigin="anonymous">
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
                <script async-udemy-dl="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" 
                integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" 
                crossorigin="anonymous"></script>
                </body>
                </html>
                ''' % (self.title, self.body)
        with open(os.path.join(self.directory, self.file_name), 'w') as f:
            f.write(data)


class UdemyStream:
    def __init__(self, type_, label, file, asset: UdemyAssetVideo):
        # content-type like this: 'video/mp4'
        self.type_ = type_
        self.label = label
        self.file = file
        self.asset = asset
        self.video_title = asset.lecture.title
        self.directory = asset.directory
        extension = self.type_.split('/')[-1]
        self.file_path = os.path.join(self.directory, asset.lecture.lecture_index +
                                      " " + asset.lecture.title + '.' + extension)
        self.part_file_path = os.path.join(self.directory, asset.lecture.lecture_index +
                                           " " + asset.lecture.title + '.' + extension + '.part')

    @coroutine_retry(sleep=3)
    async def download(self, session: aiohttp.ClientSession) -> None:
        """
        :param session:
        :return:
        """
        logging.info(f"Video {self.video_title}: start downloading")
        # video already downloaded
        if os.path.exists(self.file_path):
            return
        headers = {'User-Agent': HEADERS.get('User-Agent')}
        async with session.get(self.file, headers=headers) as resp:
            content_length = resp.content_length
        # In each iteration we download part of the video of size CHUNCKSIZE * PART_NUMBER.
        part_file_path_list = [await self.download_part(i, start, end, session) for
                               i, start, end in
                               partition(1, content_length, CHUNKSIZE * PART_NUMBER)]
        logging.info(
            f'Video {self.video_title}: '
            f'Downloading file parts completed. Now concatenate all file parts.')
        with open(self.file_path, 'ab') as f:
            for part_file_path in part_file_path_list:
                with open(part_file_path, 'rb') as part_f:
                    f.write(part_f.read())
        logging.info('Concatenate all file parts completed. Now delete part files.')
        # preserve temp files until the process of concatenating temp files
        # into one single video file is completed,
        # so that temp files are not deleted when the process of concatenating is interrupted.
        for part_file_path in part_file_path_list:
            os.remove(part_file_path)
        logging.info(f"Video {self.video_title}: end downloading")

    @coroutine_retry(sleep=3)
    async def download_part(self, part_index: int, part_start: int, part_end: int,
                            session: aiohttp.ClientSession) -> FilePath:
        """
        split part into chunks of size CHUNKSIZE and downloads chunks concurrently
        :param part_index:
        :param part_start:
        :param part_end:
        :param session:
        :return:
        """
        logging.info(f"Video {self.video_title} part {part_index + 1}: start downloading part")
        part_file_path = self.part_file_path + str(part_index + 1)
        if os.path.exists(part_file_path):
            return part_file_path
        chunk_file_path_list = await asyncio.gather(
            *[self.download_chunk(part_index, i, chunk_start, chunk_end, session) for
              i, chunk_start, chunk_end in partition(part_start, part_end, CHUNKSIZE)])
        logging.info(
            f"Video {self.video_title} part {part_index + 1}:  "
            f"Downloading file chunks completed. Now concatenate all chunk files.")
        with open(part_file_path, 'ab') as part_file:
            for chunk_file_path in chunk_file_path_list:
                with open(chunk_file_path, 'rb') as chunk_file:
                    part_file.write(chunk_file.read())
        logging.info(
            f"Video {self.video_title} part {part_index + 1}: "
            f"Concatenating all file chunks completed. Now delete chunk files")
        for chunk_file_path in chunk_file_path_list:
            os.remove(chunk_file_path)
        logging.info(
            f"Video {self.video_title} part {part_index + 1}: end downloading")

        return part_file_path

    @coroutine_retry(sleep=5)
    async def download_chunk(self, part_index: int, chunk_index: int, chunk_start: int,
                             chunk_end: int, session: aiohttp.ClientSession):
        logging.info(
            f"Video {self.video_title} part {part_index + 1} chunk {chunk_index + 1}: "
            f"start downloading")
        chunk_file_path = self.part_file_path + str(part_index + 1) + '.chunk' + str(
            chunk_index + 1)
        headers = {'User-Agent': HEADERS.get('User-Agent')}
        if os.path.exists(chunk_file_path):
            offset = os.stat(chunk_file_path).st_size
            if offset >= (chunk_end - chunk_start + 1):
                return chunk_file_path
            # Request only part of an entity. Bytes are numbered from 0
            # Range: bytes=500-999
            # but chunk_start and chunk_end here are numbered from 1
            headers['Range'] = f"bytes={chunk_start - 1 + offset}-{chunk_end - 1}"
        else:

            headers['Range'] = f'bytes={chunk_start - 1}-{chunk_end - 1}'
        with open(chunk_file_path, 'ab') as f:
            async with session.get(self.file, headers=headers) as resp:
                while True:
                    chunk = await resp.content.read(CHUNKSIZE)
                    if not chunk:
                        break
                    f.write(chunk)

        logging.info(
            f"Video {self.video_title} part {part_index + 1} chunk {chunk_index + 1}: "
            f"end downloading")
        return chunk_file_path


class UdemyCaption:
    def __init__(self, id_, title, created, file_name, status, url, source, locale_id, video_label,
                 asset_id, asset):
        self.id_ = id_
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
        self.filename = self.asset.lecture.lecture_index + ' ' \
                        + self.asset.lecture.title + '-' + locale_id.split('_')[0] + '.srt'

    def download(self):
        file_path = os.path.join(self.directory, self.filename)
        if os.path.exists(file_path):
            return
        headers = {'User-Agent': HEADERS.get('User-Agent')}
        with open(file_path, 'wb') as f:

            try:
                response = requests.get(self.url, headers=headers)
            except Exception:
                pass
            else:
                f.write(response.content)


async def entry() -> None:
    """
    download udemy course
    :return:
    """
    logging.info(f"Download starts")
    args = argment_processing()
    access_token = get_udemy_accss_token(args.cookies)
    HEADERS.update({
        'Authorization': f'Bearer {access_token}',
        'X-Udemy-Authorization': f'Bearer {access_token}',
    })
    udemy_course_info = get_udemy_course_info_by_course_name(args.course_name)
    if udemy_course_info is None:
        sys.exit("Cannot found specified udemy course.")
    else:
        output_directory = get_output_directory(args.output)
        udemy_course = UdemyCourse(udemy_course_info['id'], udemy_course_info['url'],
                                   udemy_course_info['published_title'], output_directory)
        async with aiohttp.ClientSession() as session:
            await udemy_course.download(session, args.chapter, args.lecture, args.chapter_start,
                                        args.chapter_end, args.lecture_start, args.lecture_end)
    logging.info(f"Download ends")


def main():
    asyncio.run(entry())
