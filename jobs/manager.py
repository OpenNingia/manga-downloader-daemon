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



