# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'


import os
import re
import requests

from bs4 import BeautifulSoup
from providers.generic import GenericProvider, MangaItem, ChapterItem


class MangaReader(GenericProvider):
    def __init__(self):
        super(MangaReader, self).__init__()

        self.chre = [
            re.compile(r"/(?P<nbr>\d+)$"),
            re.compile(r"/chapter-(?P<nbr>\d+).html$")
        ]

    @property
    def name(self):
        return "mangareader"

    @property
    def url(self):
        return "http://www.mangareader.net"

    def load_remote_manga_list(self):

        ml = []
        r = requests.get(self.url + '/alphabetical')

        soup = BeautifulSoup(r.text)
        for div in soup.find_all("div", class_='series_col'):
            for li in div.find_all('li'):
                ml.append(MangaItem(li.a.text, self, li.a['href']))

        return ml

    def get_chapter_list(self, manga):
        cl = []
        r = requests.get(self.url + manga.url)

        soup = BeautifulSoup(r.text)
        tab = soup.find(id='listing')
        if not tab:
            return []

        for td in tab.find_all('td'):
            for a in td.find_all('a'):
                try:
                    url = a['href']
                    # urls and paths are quite similar
                    nbr = self.extract_chapter_nbr(url)
                    cl.append(ChapterItem(
                        name=td.text.strip(),
                        manga=manga,
                        nbr=nbr,
                        provider=self,
                        url=url))

                except Exception as e:
                    print('failed to parse', a, e)
                finally:
                    break
        return cl


    def get_chapter_pages(self, chapter):
        pg = []

        r = requests.get(self.url + chapter.url)

        soup = BeautifulSoup(r.text)
        tab = soup.find(id='pageMenu')

        if not tab:
            return []

        for opt in tab.find_all('option'):
            try:
                pg.append(opt['value'])
            except Exception as e:
                print('failed to parse', opt, e)
        return pg

    def get_image_url(self, page_url):

        r = requests.get(self.url + page_url)

        soup = BeautifulSoup(r.text)

        try:
            img = soup.find(id='img')
            return img['src']
        except:
            print('failed to retrieve img url')
            return None

    ### HELPERS
    def extract_chapter_nbr(self, url):

        def apply_rx():

            try:
                m = rx.search(url)
                if not m:
                    return None
                return int(m.groups('nbr')[0])
            except Exception as e:
                return None

        for rx in self.chre:
            result = apply_rx()
            if result:
                return result
        return 0

