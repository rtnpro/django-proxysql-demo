import logging

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from pebble import ProcessPool

from counter.models import Counter

logger = logging.getLogger('counter')

def run_savepoints(bucket_id):
    for i in range(1, 100):
        connections.close_all()
        try:
            with transaction.atomic():
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info('run_savepoints index: %s\tinitial count: %s', i, bucket.count)
                bucket.count = i
                bucket.save()

                try:
                    with transaction.atomic():
                        bucket = Counter.objects.get(bucket=bucket_id)
                        if bucket.count != i:
                            logger.error('run_savepoints index: %s\texpected_count: %s \tcount: %s', i, i, bucket.count)

                        bucket.count = i + 1
                        bucket.save()

                        bucket = Counter.objects.get(bucket=bucket_id)
                        if bucket.count != (i + 1):
                            logger.error('run_savepoints index: %s\texpected_count: %s \tcount: %s', i, i + 1, bucket.count)

                        if bucket.count % 2 != 0:
                            raise
                except:
                    pass

                bucket = Counter.objects.get(bucket=bucket_id)
                if bucket.count != (i + 1 * (i % 2)):
                    logger.error('run_savepoints index: %s\texpected_count: %s \tcount: %s', i, i + (1 * (i % 2)), bucket.count)
                logger.info('run_savepoints index: %s\t count: %s', i, bucket.count)
        except Exception as e:
            logger.exception(e)


def run_atomic_transactions(bucket_id):
    for i in range(200, 300):
        connections.close_all()
        try:
            with transaction.atomic():
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info('run_atomic_transactions index: %s\tinitial count: %s', i, bucket.count)
                bucket.count = i
                bucket.save()
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info('run_atomic_transactions index: %s\tcount: %s', i, bucket.count)
        except Exception as e:
            logger.exception(e)

class Command(BaseCommand):

    def handle(self, *args, **options):
        bucket_id = 1

        pool = ProcessPool(max_workers=2)
        pool._start_pool()

        future_1 = pool.schedule(
            run_atomic_transactions,
            args=(bucket_id,)
        )
        future_2 = pool.schedule(
            run_savepoints,
            args=(bucket_id,)
        )
        pool.close()
        pool.join()
