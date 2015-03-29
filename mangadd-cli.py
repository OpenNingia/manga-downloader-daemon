#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'


__version__ = '0.1'

import sys
import json
import argparse
import requests


def parse_args():
    parser = argparse.ArgumentParser(
        description='Manga downloader daemon v{}'.format(__version__))

    # valid commands are
    # n: new manga
    # d: download manga
    parser.add_argument('command', metavar='CMD', type=str,
                        help='command to execute')

    return parser.parse_args()


def list_jobs():
    r = requests.get('http://192.168.0.15:8888/jobs/list')
    if r.status_code != 200:
        print('cannot retrieve job list', r.status_code)
        return

    # print(r.headers['content-type'])
    # print(r.encoding)
    payload = r.json()

    try:

        print('JOB LIST\n')

        for j in payload['jobs']:
            print(j)
    except Exception as e:
        print('cannot retrieve job list', e)


def add_job():
    url = input("manga url: ")
    cfrom = -1
    cto = -1
    vol = -1

    try:
        cfrom = int(input("chapter from [first]: "))
    except:
        cfrom = -1

    try:
        cto = int(input("chapter to [last]: "))
    except:
        cto = -1

    try:
        vol = int(input("volume: "))
    except:
        vol = -1

    obj = {
        'url': url,
        'from': cfrom,
        'to': cto,
        'volume': vol,
        'format': 'cbz',
        'profile': 'kobo_aura_hd'
    }

    r = requests.post('http://192.168.0.15:8888/jobs/add', {'body': json.dumps(obj)})
    print(r.status_code)


def remove_job():
    jobid = -1

    try:
        jobid = int(input("job id: "))
    except:
        jobid = -1

    obj = {
        'jobid': jobid
    }

    r = requests.post('http://192.168.0.15:8888/jobs/del', {'body': json.dumps(obj)})
    print(r.status_code)


def main(args):

    if args.command == 'l':
        sys.exit(list_jobs())
    elif args.command == 'a':
        sys.exit(add_job())
    elif args.command == 'r':
        sys.exit(remove_job())
    else:
        print('unknown command: {}'.format(args.command))

if __name__ == '__main__':
    main(parse_args())
