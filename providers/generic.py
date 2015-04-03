# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import os
import sys
import json
import util
import time
import shutil
import requests

from jobs.manager import JobManager

# pyprind is optional
try:
    import pyprind
except:
    pass

from bll.corruptiondetect import is_image_corrupted


class MangaItem(object):

    def __init__(self, name, provider, url):
        self.name = name
        self.url = url
        self.provider = provider
        self.id_ = None

        # cache
        self._chapter_cache = None

    @property
    def chapters(self):
        if not self._chapter_cache:
            self._chapter_cache = self.provider.get_chapter_list(self)
        return self._chapter_cache

    def __eq__(self, other):
        if not isinstance(other, MangaItem):
            return False
        return other.url == self.url and other.provider == self.provider


class ChapterItem(object):

    def __init__(self, name, manga, nbr, provider, url=None, vol=0):
        self.name = name
        self.manga = manga
        self.provider = provider
        self.nbr = nbr
        self.url = url
        self.vol = vol

        # cache
        self._page_cache = None

    @property
    def pages(self):
        if not self._page_cache:
            self._page_cache = self.provider.get_chapter_pages(self)
        return self._page_cache


class DownloadProfiler(object):
    def __init__(self):
        self.time = None
        self.end_time = None
        self.downloaded = 0

    def begin(self):
        self.time = time.clock()
        self.downloaded = 0

    def end(self):
        self.end_time = time.clock()

    def add(self, count):
        self.downloaded += count

    def bytes_per_seconds(self, partial=False):
        elapsed = 0
        if partial:
            elapsed = time.clock() - self.time
        else:
            elapsed = self.end_time - self.time

        if elapsed == 0:
            return 0
        return self.downloaded / elapsed


class GenericProvider(object):
    def __init__(self):
        self.manga_list_ = []
        self.cache_ = os.path.expanduser(
            "~/.mangadd/providers/"
            + self.name
            + '/mangalist.json')
        self.profiler = DownloadProfiler()
        self.load_cached_manga_list()

        self.progress_text = ''

    @property
    def mangalist(self):
        return self.manga_list_

    @property
    def name(self):
        return "n/a"

    @property
    def url(self):
        return ""

    # OVERRIDES
    def load_remote_manga_list(self):
        pass

    def get_chapter_list(self, manga):
        pass

    def get_chapter_pages(self, chapter):
        pass

    def get_image_url(self, page_url):
        pass

    # COMMON
    def download_manga(self, manga, settings):
        """download all missing chapters"""

        for c in manga.chapters:
            self.download_chapter(c, settings)

    def download_chapter(self, chapter, settings, job=None):
        """download all missing pages from chapter"""

        print('downloading chapter: {} - {}'.format(chapter.nbr, chapter.url))

        manga_dir = os.path.join(settings.appcfg.download_dir,
                                 chapter.manga.name)

        chapter_dir = os.path.join(manga_dir,
                                   settings.appcfg.chapter_fmt.format(ch=chapter.nbr, nm=util.remove_invalid_path_chars(chapter.name)))

        if job.volume > 0:
            volume_dir = os.path.join(manga_dir,
                                      settings.appcfg.volume_dir_fmt.format(voln=job.volume, manga=chapter.manga.name))

            chapter_dir = os.path.join(volume_dir,
                                       settings.appcfg.chapter_fmt.format(
                                           ch=chapter.nbr, nm=util.remove_invalid_path_chars(chapter.name)))

        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        for i, pg in enumerate(chapter.pages):

            self.progress_text = 'page {} of {}'.format(i, len(chapter.pages))

            image_path = os.path.join(chapter_dir,
                                      settings.appcfg.page_fmt.format(pg=i))

            if self.download_image(self.get_image_url(pg), image_path):

                if job:
                    job.chapter = chapter.nbr
                    job.pages_downloaded += 1
                    JobManager.instance().save_job(job)

    def download_image(self, url, save_path):

        ext = url.rpartition('.')[2]

        image_path = "{}.{}".format(save_path, ext)
        image_downloading_path = "{}.mdd".format(image_path, ext)

        # assume already downloaded
        if os.path.exists(image_path):
            return True

        retries = 0
        pbar = None

        while True:

            try:
                r = requests.get(url, stream=True)
                if r.status_code == 200:

                    try:
                        pbar = pyprind.ProgBar(int(r.headers['content-length']),
                                               title=self.progress_text)
                    except:
                        pbar = None

                    self.profiler.begin()

                    with open(image_downloading_path, 'wb') as f:
                        for chunk in r.iter_content():
                            f.write(chunk)
                            self.profiler.add(len(chunk))

                            #sys.stdout.write(
                            #    '{} KB/s\r'.format(
                            #        int(self.profiler.bytes_per_seconds(True)/1024)))
                            if pbar:
                                pbar.update(len(chunk))

                            #sys.stdout.flush()

                    self.profiler.end()

                    # if image is not corrupted
                    # remove downloading extension
                    # and exit the cycle
                    if not is_image_corrupted(image_downloading_path):
                        shutil.move(image_downloading_path, image_path)
                        break

            except Exception as e:
                print('download error: {}'.format(e))

            if retries > 3:
                print('cannot download image from', url)
                return False

            retries += 1

        #print('downloaded page: {}, speed: {:G} Kb/s'.format(url,
        #      self.profiler.bytes_per_seconds()/1024))
        return True

    def update_manga_list(self):

        self.manga_list_ = self.load_remote_manga_list()
        self.save_manga_list()

    def load_cached_manga_list(self):

        if not os.path.exists(self.cache_):
            return

        self.manga_list_ = []
        try:
            with open(self.cache_, 'rt', encoding='utf-8') as fp:
                jobj = json.load(fp)
                for md in jobj:
                    self.mangalist.append(
                        MangaItem(md['name'],
                                  self,
                                  md['url']))
        except:
            pass

    def save_manga_list(self):

        dir_ = os.path.expanduser("~/.mangadd/providers/" + self.name)
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        with open(self.cache_, 'wt', encoding='utf-8') as fp:

            jobj = []
            for m in self.mangalist:
                md = {}
                md['name'] = m.name
                md['url'] = m.url
                jobj.append(md)
            json.dump(jobj, fp)


    def __eq__(self, other):
        if not isinstance(other, GenericProvider):
            return False
        return self.url == other.url
