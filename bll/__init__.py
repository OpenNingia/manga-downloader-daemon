# -*- coding: utf-8 -*-

import os
import json
import config
import providers


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

