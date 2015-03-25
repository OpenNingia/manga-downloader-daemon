# -*- coding: utf-8 -*-

import os
import sys
import json
import glob


class SettingsReader(object):
    def __init__(self):
        self.appdir = os.path.expanduser("~/.mangadd")
        self.appcfg = None
        self.manga_cfg = []

        if not os.path.exists(self.appdir):
            os.makedirs(self.appdir)

        for jf in glob.glob(self.appdir + "/*.json"):
            fn = os.path.basename(jf)

            print('parsing config file', jf)
            if fn == 'config.json':
                self.appcfg = AppSettingsReader(jf)

        for jf in glob.glob(self.appdir + "/manga/*.json"):
            fn = os.path.basename(jf)
            print('parsing manga config file', jf)
            self.manga_cfg.append(MangaSettingsReader(jf))


class AppSettingsReader(object):
    """
    {
        "download_dir": "/home/downloads/manga",
        "chapter_fmt": "{ch:05G}",
        "page_fmt": "{pg:05G}",
        "volume_dir_fmt": "[VOL {voln:03G}] {manga}"
    }
    """

    def __init__(self, location):
        if not os.path.exists(location):
            raise Exception('app config not found')

        self.download_dir = os.path.expanduser("~/.mangadd/downloads")
        self.chapter_fmt = "{ch:05G}"
        self.page_fmt = "{pg:05G}"
        self.volume_dir_fmt = "[VOL {voln:03G}] {manga}"

        with open(location, 'rt') as fp:
            jd = json.load(fp)

            if 'download_dir' in jd:
                self.download_dir = jd['download_dir']
            if 'chapter_fmt' in jd:
                self.chapter_fmt = jd['chapter_fmt']
            if 'page_fmt' in jd:
                self.page_fmt = jd['page_fmt']
            if 'volume_dir_fmt' in jd:
                self.volume_dir_fmt = jd['volume_dir_fmt']

        print('download dir', self.download_dir)
        print('chapter format', self.chapter_fmt,
              'example. ch 1', self.chapter_fmt.format(ch=1))
        print('volume format', self.volume_dir_fmt,
              'example. vol 1', self.volume_dir_fmt.format(voln=1, manga='Naruto'))


class MangaSettingsReader(object):
    """
    {
        "name": "Kingdom",
        "provider": "mangareader",
        "url": "http://www.mangareader.net/1730/kingdom.html",
        "id": "1730"
    }
    """

    def __init__(self, location):
        if not os.path.exists(location):
            raise Exception('manga config not found')

        self.name = ""
        self.provider = ""
        self.url = ""
        self.id = ""

        with open(location, 'rt') as fp:
            jd = json.load(fp)

            if 'name' in jd:
                self.name = jd['name']
            if 'provider' in jd:
                self.provider = jd['provider']
            if 'url' in jd:
                self.url = jd['url']
            if 'id' in jd:
                self.id = jd['id']
