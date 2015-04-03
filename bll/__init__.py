# -*- coding: utf-8 -*-

import os
import sys
import json
import util
import config
import providers

# logging
import logging
import logging.handlers

def create_manga(args):
    """create directory and manifest for a new download"""

    cc = None
    manga_url = None
    #manga_prov = None
    home_dir = os.path.expanduser("~/.mangadd")

    try:
        manga_name = args.manganm
        manga_url = args.mangauri
    except Exception as e:
        print(e)
        return 1

    manga_dir = os.path.join(home_dir, 'manga')

    if not os.path.exists(manga_dir):
        os.makedirs(manga_dir)

    manifest_file = os.path.join(manga_dir, '{}.json'.format(manga_name))

    with open(manifest_file, 'wt') as fp:

        contents = {
            "name": manga_name,
            "url": manga_url,
            "id": ""
        }

        json.dump(contents, fp)

        return 0


def download_manga(args):

    # search local manga
    cfg = config.SettingsReader()
    local_manga = None

    print(cfg.manga_cfg)

    try:
        local_manga = [x for x in cfg.manga_cfg if x.name == args.manganm][0]
    except:
        raise Exception('manga not found, use create-manga feature first')

    manga_uri = local_manga.url

    providers.init_providers()
    prov = providers.by_url(manga_uri)

    if prov is None:
        raise Exception('url {} is unsupported'.format(manga_uri))


    print('search manga @ {}'.format(manga_uri))

    # remove provider root uri
    manga_uri = manga_uri.replace(prov.url, '')

    # search provider manga
    manga = [x for x in prov.mangalist if x.url == manga_uri]
    if not len(manga):
        # update manga list
        prov.update_manga_list()

    manga = [x for x in prov.mangalist if x.url == manga_uri]
    if not len(manga):
        # manga not found on this provider
        raise Exception('manga not found, use another provider')

    from_ = args.begin

    for c in manga[0].chapters:

        if from_ > 0 and c.nbr < from_:
            continue

        prov.download_chapter(c, cfg)


def create_job_resume_info(manga, job):
    """create directory and manifest for a new download"""

    manga_url = None
    #manga_prov = None
    home_dir = os.path.expanduser("~/.mangadd")

    try:
        manga_name = manga.name
        manga_url = job.manga_url
    except Exception as e:
        print(e)
        return 1

    manga_dir = os.path.join(home_dir, 'manga')

    if not os.path.exists(manga_dir):
        os.makedirs(manga_dir)

    manifest_file = os.path.join(manga_dir, '{}.json'.format(manga_name))

    with open(manifest_file, 'wt') as fp:

        contents = {
            "name": manga_name,
            "url": manga_url,
            "id": job.jobid,
            "from": job.chapter_from,
            "to": job.chapter_to,
            "chapter": job.chapter_from,
        }

        json.dump(contents, fp)

        return contents


def download_manga_job(job):

    log = util.setup_http_logger('jobs.bll')

    # search manga provider
    providers.init_providers()
    prov = providers.by_url(job.manga_url)

    if not prov:
        log.error('manga url not supported: {}'.format(job.manga_url))
        return False

    # remove provider root uri
    rel_uri = job.manga_url.replace(prov.url, '')

    # search online manga
    online_manga = [x for x in prov.mangalist if x.url == rel_uri]

    if not len(online_manga):
        prov.update_manga_list()
        online_manga = [x for x in prov.mangalist if x.url == rel_uri]
        if not len(online_manga):
            log.error('manga not found on provider: {}'.format(rel_uri))
            return False

    online_manga = online_manga[0]

    from_ = max(job.chapter, job.chapter_from)
    to_ = job.chapter_to if job.chapter_to > 0 else sys.maxsize

    chapters_left = [x for x in online_manga.chapters
                             if from_ <= x.nbr <= to_]

    job_chapters = [x for x in online_manga.chapters
                    if job.chapter_from <= x.nbr <= job.chapter_to]

    already_downloaded = util.list_diff(job_chapters, chapters_left)

    job.pages_count = sum([len(x.pages) for x in job_chapters])

    if len(already_downloaded):
        job.pages_downloaded = sum([len(x.pages) for x in already_downloaded])
    else:
        job.pages_downloaded = 0

    log.info('pages to download: {}'.format(job.pages_count))
    log.info('pages already downloaded: {}'.format(job.pages_downloaded))

    cfg = config.SettingsReader()

    for c in chapters_left:
        prov.download_chapter(c, cfg, job)

    return True
