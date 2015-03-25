# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import os
import json
import requests

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


class GenericProvider(object):
    def __init__(self):
        self.manga_list_ = []
        self.cache_ = os.path.expanduser("~/.mangadd/providers/" + self.name + '/mangalist.json')
        self.load_cached_manga_list()

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

    def download_chapter(self, chapter, settings):
        """download all missing pages from chapter"""

        manga_dir = os.path.join(settings.appcfg.download_dir,
                                 chapter.manga.name)

        chapter_dir = os.path.join(manga_dir,
                                   settings.appcfg.chapter_fmt.format(
                                       ch=chapter.nbr))

        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        for i, pg in enumerate(chapter.pages):

            image_path = os.path.join(chapter_dir,
                                      settings.appcfg.page_fmt.format(pg=i))

            self.download_image(self.get_image_url(pg), image_path)


    def download_image(self, url, save_path):

        ext = url.rpartition('.')[2]

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open("{}.{}".format(save_path, ext), 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            print('cannot download image from', url)

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