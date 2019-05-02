import logging
import time

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from pebble import ProcessPool

from counter.models import Counter

logger = logging.getLogger('counter')

def run_savepoints(name, bucket_id):
    for i in range(1, 4):
        connections.close_all()
        try:
            with transaction.atomic():
                bucket = Counter.objects.get(bucket=bucket_id)
                initial_count = bucket.count

                transaction_type = 'outer'

                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    'enter',  # event
                    initial_count)
                time.sleep(1.5)

                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                time.sleep(1)

                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                bucket.count = i
                bucket.save()
                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                try:
                    with transaction.atomic():
                        transaction_type = 'inner'
                        bucket = Counter.objects.get(bucket=bucket_id)

                        logger.info(
                            '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                            name,
                            i,
                            transaction_type,
                            'enter',  # event
                            bucket.count)

                        if bucket.count != i:
                            logger.error(
                                '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                                name,
                                i,
                                transaction_type,
                                'expected: %s' % i,  # event
                                'Got: %s' % bucket.count)

                        bucket.count = i + 1
                        bucket.save()

                        bucket = Counter.objects.get(bucket=bucket_id)

                        logger.info(
                            '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                            name,
                            i,
                            transaction_type,
                            'save',  # event
                            bucket.count)

                        if bucket.count != (i + 1):
                            logger.error(
                                '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                                name,
                                i,
                                transaction_type,
                                'expected: %s' % i + 1,  # event
                                'Got: %s' % bucket.count)


                        if bucket.count % 2 != 0:
                            raise
                except:
                    pass
                finally:
                    bucket = Counter.objects.get(bucket=bucket_id)
                    logger.info(
                        '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                        name,
                        i,
                        transaction_type,
                        'exit',  # event
                        bucket.count)
                    transaction_type = 'outer'

                time.sleep(1)

                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)
                if bucket.count != (i + 1 * (i % 2)):
                    logger.error(
                        '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                        name,
                        i,
                        transaction_type,
                        'expected: %s' % (i + (1 * (i % 2))),  # event
                        'Got: %s' % bucket.count)
                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    'exit',  # event
                    bucket.count)
        except Exception as e:
            logger.exception(e)
        time.sleep(0.5)


def run_atomic_transactions(name, bucket_id):
    for i in range(200, 204):
        connections.close_all()
        try:
            with transaction.atomic():
                transaction_type = 'main'
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    'enter',  # event
                    bucket.count)
                bucket.count = i
                time.sleep(1)
                bucket.save()
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
                    name,
                    i,
                    transaction_type,
                    'save',  # event
                    bucket.count)
                time.sleep(1)
        except Exception as e:
            logger.exception(e)
        bucket = Counter.objects.get(bucket=bucket_id)
        logger.info(
            '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
            name,
            i,
            transaction_type,
            'exit',  # event
            bucket.count)
        time.sleep(1)

        bucket = Counter.objects.get(bucket=bucket_id)
        logger.info(
            '%-10s\t%-10s\t%-10s\t%-10s\t%-10s',
            name,
            i,
            transaction_type,
            '',  # event
            bucket.count)

        time.sleep(1)

class Command(BaseCommand):

    def handle(self, *args, **options):
        bucket_id = 1

        pool = ProcessPool(max_workers=2)
        pool._start_pool()

        future_1 = pool.schedule(
            run_atomic_transactions,
            args=('ATOMIC', bucket_id,)
        )
        future_2 = pool.schedule(
            run_savepoints,
            args=('SAVEPOINT', bucket_id,)
        )
        pool.close()
        pool.join()
