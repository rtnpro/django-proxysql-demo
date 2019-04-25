import functools
import logging
import os
import random
import signal
import time

from concurrent import futures
from django import db
from django.db import transaction

from pebble import ProcessPool

from counter.models import Counter

logger = logging.getLogger('counter')
BUCKET_RANGE = range(1, 1000)


def close_all_connections():
    db.connections.close_all()


def handle_sigterm(signum, frame):
    logger.warning('Handling sigterm')
    close_all_connections()


def initialize_worker():
    close_all_connections
    signal.signal(signal.SIGTERM, handle_sigterm)


def incr(bucket_id, sleep=0.01):
    pid = os.getpid()
    logger.debug('Increment\tpid:{}\tbucket:{}'.format(pid, bucket_id))
    count = None
    try:
        with transaction.atomic():
            counter, created = Counter.objects.get_or_create(bucket=bucket_id)
            counter.count += 1
            logger.debug('Sleeping for {}\tpid: {}\tbucket: {}'.format(sleep, pid, bucket_id))
            time.sleep(sleep)
            counter.save()
            count = counter.count
    except Exception as e:
        logger.warning('counter: {}, created: {}'.format(counter, created))
        logger.exception('IncrementError\tpid: {}\tbucket: {}\n{}'.format(pid, bucket_id, e))
    finally:
        close_all_connections()
    return count


class CounterDaemon(object):

    def __init__(self, workers=1, poll_interval=None, max_tasks=100, task_timeout=0.1,
                 task_default_sleep=0.01, task_sleep_rand_range=(1, 20)):
        self.workers = workers
        self.poll_interval = poll_interval
        self.max_tasks = max_tasks
        self.task_timeout = task_timeout
        self.task_default_sleep = task_default_sleep
        self.task_sleep_rand_range = task_sleep_rand_range

        self.pool = ProcessPool(max_workers=self.workers, max_tasks=self.max_tasks)
        self.pool._start_pool()

    def done_callback(self, bucket_id, future):
        pid = os.getpid()
        try:
            result = future.result()
            logger.debug('Result: {}\tpid: {}\tbucket: {}'.format(result, pid, bucket_id))
        except futures.TimeoutError as e:
            logger.warning('TimeoutError\tpid: {}\tbucket: {}'.format(pid, bucket_id))
        except futures.CancelledError:
            return
        except Exception as e:
            logger.exception('TaskError\t pid: {}\tbucket: {}\tError: {}'.format(pid, bucket_id, e))

    def run_once(self):
        for bucket_id in random.sample(BUCKET_RANGE, self.workers):
            sleep = self.task_default_sleep * random.randint(*self.task_sleep_rand_range)
            future = self.pool.schedule(
                incr,
                args=(bucket_id,),
                kwargs={'sleep': sleep},
                timeout=self.task_timeout
            )
            future.add_done_callback(functools.partial(self.done_callback, bucket_id))

    def run_forever(self):
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.exception('RunOnceError: {}'.format(e))
            time.sleep(self.poll_interval or (3 * self.task_timeout))

    def start(self):
        try:
            self.run_forever()
        except Exception as e:
            logger.exception('Error during running daemon: {}'.format(e))
            self.pool.close()
            time.sleep(10)
            self.pool.stop()
        finally:
            self.pool.join()
