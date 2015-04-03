#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = '0.1'

import sys
import config
import providers
import argparse

from bll import create_manga, download_manga


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


def parse_args():
    parser = argparse.ArgumentParser(
        description='Manga downloader daemon v{}'.format(__version__))

    # valid commands are
    # n: new manga
    # d: download manga
    parser.add_argument('command', metavar='CMD', type=str,
                        help='command to execute')

    parser.add_argument('--manga', dest='manganm',
                        help='name of the manga, without spaces')

    parser.add_argument('--from', dest='begin', type=int, default=-1,
                        help='number of chapter')

    #parser.add_argument('--output', dest='output',
    #                    help='download directory')

    parser.add_argument('--url', dest='mangauri',
                        help='manga url')

    return parser.parse_args()


def main(args):

    if args.command == 'n':
        sys.exit(create_manga(args))
    elif args.command == 'd':
        sys.exit(download_manga(args))
    else:
        print('unknown command: {}'.format(args.command))

if __name__ == '__main__':
    main(parse_args())
