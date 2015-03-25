#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import config
import providers


def test():
    cfg = config.SettingsReader()

    mr = providers.by_name('mangareader')

    if not len(mr.mangalist):
        mr.update_manga_list()

    manga = [x for x in mr.mangalist if x.name == 'Kingdom']
    if len(manga):
        kingdom = manga[0]
        print('{} has {} chapters'.format(kingdom.name, len(kingdom.chapters)))

        first_chapter = kingdom.chapters[0]
        print('chapter has {} pages'.format(len(first_chapter.pages)))

        mr.download_chapter(first_chapter, cfg)


def main():
    pass


if __name__ == '__main__':
    main()
