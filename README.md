# Manga Downloader Daemon
Downloads manga

## Features
  * support for various manga providers
    + MangaReader
    + MangaHere
    + Batoto
    + KissManga
    + etc...
  * automatic check for new chapter
  * background download of new chapter
  * api to group chapters into volumes
  * api to compress a volume into a cbz
  * ebook optimization

# Inspirations
  * For manga downloader capabilities
    + Hakuneku
  * For cbz and ebook optimization
    + KindleComicConverter

# Specifics
Mangadd should parse json configuration files placed in /home/.mangadd directory.
An example Json file for Kingdom manga would be:

```json
{
    "name": "Kingdom",
    "provider": "mangareader",
    "url": "http://www.mangareader.net/1730/kingdom.html",
    "id": "1730"
}
```

Also a special file called config.json should be place in /home/.mangadd directory
to overwrite default configuration settings.

```json
{
    "download_dir": "/home/downloads/manga",
    "chapter_fmt": "{ch:00000}",
    "volume_dir_fmt": "[VOL {voln:000}] {manga}"
}
```

The chapter are to be downloaded in the "download_dir" directory, and the directory tree
should look as follow:

```
root >
    manga_name >
        00001 >
            00001.jpg
            00002.jpg
            ...
        00002 >
            00001.jpg
            00002.jpg
            ...
    another_manga >
        ...