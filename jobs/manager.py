# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

from util.singleton import Singleton

class JobItem(object):

    JOB_STATUS_STOPPED = 0
    JOB_STATUS_PAUSED = 1
    JOB_STATUS_QUEUED = 2
    JOB_STATUS_RUNNING = 3
    JOB_STATUS_ERROR = 0xFF

    def __init__(self):
        self.jobid = 0
        self.label = ''
        self.status = JobItem.JOB_STATUS_STOPPED
        self.progress = 0

    def from_json(self, obj):
        if 'label' in obj:
            self.label = obj['label']

    def json(self):
        return {'jobid': self.jobid, 'label': self.label,
                'status': self.status, 'progress': self.progress}

class DownloadJobItem(JobItem):
    def __init__(self):
        super(DownloadJobItem, JobItem).__init__()

        self.provider_name = ''
        self.manga_url = ''
        self.chapter_pattern = ''


class PackJobItem(JobItem):
    def __init__(self):
        super(PackJobItem, JobItem).__init__()

        self.format = 'cbz'
        self.manga_name = ''
        self.volume = 0
        self.start = 0
        self.end = 0


class DownloadAndPackJobItem(JobItem):
    def __init__(self):
        super(DownloadAndPackJobItem, self).__init__()

        self.manga_url = ''
        self.chapter_from = -1
        self.chapter_to = -1
        self.volume = -1

        self.profile = 'kobo_aura_hd'
        self.format = 'cbz'

    def from_json(self, obj):
        super(DownloadAndPackJobItem, self).from_json(obj)

        self.manga_url = obj['url']

        if 'from' in obj:
            self.chapter_from = int(obj['from'])
        if 'to' in obj:
            self.chapter_to = int(obj['to'])
        if 'volume' in obj:
            self.volume = int(obj['volume'])
        if 'volume' in obj:
            self.profile = obj['volume']
        if 'volume' in obj:
            self.format = obj['volume']

    def json(self):

        ret = super(DownloadAndPackJobItem, self).json()
        ret['url'] = self.manga_url
        ret['from'] = self.chapter_from
        ret['to'] = self.chapter_to
        ret['volume'] = self.volume
        ret['profile'] = self.profile
        ret['format'] = self.format

        return ret


@Singleton
class JobManager(object):

    def __init__(self):
        self.jobs = []
        self.progressive = 1

    def add_job(self, jobitem):
        jobitem.jobid = self.progressive
        self.progressive += 1
        self.jobs.append(jobitem)

    def remove_job(self, jobid):
        j = [x for x in self.jobs if x.jobid == jobid]
        for x in j:
            self.jobs.remove(x)

    @property
    def joblist(self):
        return self.jobs
