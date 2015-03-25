# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

from PIL import Image


def is_image_corrupted(path):
    try:
        img = Image.open(path)
        img.verify()
        img = Image.open(path)
        img.load()
        return False
    except Exception:
        return True
