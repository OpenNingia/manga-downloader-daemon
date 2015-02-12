# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

PROVIDER_MAP = {}


def by_name(nm):
    if nm in PROVIDER_MAP:
        return PROVIDER_MAP[nm]
    return None


def init_providers():
    from providers.mangareader import MangaReader
    PROVIDER_MAP['mangareader'] = MangaReader()

init_providers()

