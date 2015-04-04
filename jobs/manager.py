# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import os
import config
from util.singleton import Singleton

import util
import glob
import json
import multiprocessing as mp

# logging
import logging
import logging.handlers


class JobItem(object):

    JOB_STATUS_STOPPED = 0
    JOB_STATUS_PAUSED = 1
    JOB_STATUS_QUEUED = 2
    JOB_STATUS_RUNNING = 3
    JOB_STATUS_COMPLETED = 4
    JOB_STATUS_ERROR = 0xFF

    def __init__(self):
        self.jobid = 0
        self.label = ''
        self.status = JobItem.JOB_STATUS_STOPPED

    def from_json(self, obj):
        if 'label' in obj:
            self.label = obj['label']
        if 'jobid' in obj:
            self.jobid = int(obj['jobid'])
        if 'status' in obj:
            self.status = int(obj['status'])

    @property
    def progress(self):
        return 0

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
        self.chapter = 1
        self.volume = -1
        self.pages_count = 0
        self.pages_downloaded = 0
        self.pages_per_second = 0
        self.download_eta = 0

        self.profile = 'kobo_aura_hd'
        self.format = 'cbz'

    @property
    def progress(self):
        if self.pages_count == 0:
            return 0
        return int(self.pages_downloaded / self.pages_count * 100)


    def from_json(self, obj):
        super(DownloadAndPackJobItem, self).from_json(obj)

        self.manga_url = obj['url']

        if 'from' in obj:
            self.chapter_from = int(obj['from'])
        if 'to' in obj:
            self.chapter_to = int(obj['to'])
        if 'volume' in obj:
            self.volume = int(obj['volume'])
        if 'profile' in obj:
            self.profile = obj['profile']
        if 'format' in obj:
            self.format = obj['format']
        if 'chapter' in obj:
            self.chapter = int(obj['chapter'])
        if 'pages_count' in obj:
            self.pages_count = int(obj['pages_count'])
        if 'pages_downloaded' in obj:
            self.pages_downloaded = int(obj['pages_downloaded'])
        if 'pages_per_second' in obj:
            self.pages_per_second = float(obj['pages_per_second'])
        if 'download_eta' in obj:
            self.download_eta = obj['download_eta']

        return self

    def json(self):

        ret = super(DownloadAndPackJobItem, self).json()
        ret['url'] = self.manga_url
        ret['from'] = self.chapter_from
        ret['to'] = self.chapter_to
        ret['volume'] = self.volume
        ret['profile'] = self.profile
        ret['format'] = self.format
        ret['chapter'] = self.chapter
        ret['pages_count'] = self.pages_count
        ret['pages_downloaded'] = self.pages_downloaded
        ret['pages_per_second'] = self.pages_per_second
        ret['download_eta'] = self.download_eta

        return ret


def run_job(queue):
    import bll

    log = util.setup_http_logger('job.runner')

    j = queue.get()

    log.info('job {} status. {} => {} (RUNNING)'.format(j.jobid, j.status, JobItem.JOB_STATUS_RUNNING))
    j.status = JobItem.JOB_STATUS_RUNNING

    try:
        bll.download_manga_job(j)
        log.info('job {} status. {} => {} (COMPLETED)'.format(j.jobid, j.status, JobItem.JOB_STATUS_COMPLETED))
        j.status = JobItem.JOB_STATUS_COMPLETED
    except Exception as e:
        log.info('job {} status. {} => {} (ERROR)'.format(j.jobid, j.status, JobItem.JOB_STATUS_COMPLETED))
        j.status = JobItem.JOB_STATUS_ERROR
        log.exception(e)

    JobManager.instance().save_job(j)


@Singleton
class JobManager(object):

    def __init__(self):
        self.jobs = []
        self.procs = []
        self.queue = mp.Queue(maxsize=3)
        self.progressive = 1

    def add_job(self, jobitem):

        if jobitem.jobid == 0:
            jobitem.jobid = self.progressive
            self.progressive += 1

        if jobitem.chapter < 0:
            if jobitem.chapter_from > 0:
                jobitem.chapter = jobitem.chapter_from
            else:
                jobitem.chapter = 1

        self.jobs.append(jobitem)

        if jobitem.status != JobItem.JOB_STATUS_COMPLETED:
            jobitem.status = JobItem.JOB_STATUS_PAUSED

            if not self.queue.full():
                self.queue_job(jobitem)

        self.save_job(jobitem)

    def remove_job(self, jobid):
        j = [x for x in self.jobs if x.jobid == jobid]
        for x in j:
            self.jobs.remove(x)

    def run_once(self):

        log = util.setup_http_logger('job.manager')

        self.check_procs()

        self.reload_job_status()

        if self.queue.empty():
            return

        try:
            p = mp.Process(target=run_job, args=(self.queue,))
            p.daemon = True
            p.start()
            self.procs.append(p)
        except Exception as e:
            log.exception(e)

    def reload_job_status(self):
        cfg = config.SettingsReader()

        for j in self.joblist:
            jf = os.path.join(cfg.appdir, 'jobs', '{:09G}.json'.format(j.jobid))
            if not os.path.exists(jf):
                continue

            with open(jf, 'rt') as fp:
                try:
                    j.from_json(json.load(fp))
                except Exception as e:
                    print('could not update job: {}'.format(j.jobid), e)

    def check_procs(self):

        dead_procs = [x for x in self.procs if not x.is_alive()]
        for p in dead_procs:
            self.procs.remove(p)
            self.on_job_finished()

    def stop(self):
        pass

    def on_job_finished(self):
        paused_jobs = [x for x in self.jobs
                       if x.status == JobItem.JOB_STATUS_PAUSED]

        if len(paused_jobs):
            self.queue_job(paused_jobs[0])

    def queue_job(self, job):
        job.status = JobItem.JOB_STATUS_QUEUED
        self.queue.put(job)

    def save_job(self, job):
        cfg = config.SettingsReader()
        job_file = os.path.join(cfg.appdir, 'jobs',
                                '{:09G}.json'.format(job.jobid))

        with open(job_file, 'wt') as fp:
            json.dump(job.json(), fp)

    def load_jobs(self):
        cfg = config.SettingsReader()

        if not os.path.exists(cfg.appdir + "/jobs"):
            os.makedirs(cfg.appdir + "/jobs")

        for jf in glob.glob(cfg.appdir + "/jobs/*.json"):

            print('loading job: {}'.format(jf))

            with open(jf, 'rt') as fp:
                try:
                    job = DownloadAndPackJobItem().from_json(json.load(fp))
                    # job.status = JobItem.JOB_STATUS_PAUSED
                    self.add_job(job)
                except Exception as e:
                    print('could not load job', e)

        try:
            self.progressive = max([x.jobid for x in self.joblist]) + 1
        except:
            self.progressive = 1

    @property
    def joblist(self):
        return self.jobs
