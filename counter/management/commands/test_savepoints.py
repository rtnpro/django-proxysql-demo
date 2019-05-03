import logging
import time

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from pebble import ProcessPool

from counter.models import Counter

logger = logging.getLogger('counter')

def run_savepoints(name, bucket_id):
    bucket, _ = Counter.objects.get_or_create(bucket=bucket_id)
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
    bucket, _ = Counter.objects.get_or_create(bucket=bucket_id)
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
    """
    This command tests running two processes in parallel running transactions.
    `run_atomic_transactions` runs plain `atomic` transactions and
    `run_savepoints` runs nested `atomic` transactions which internally uses
    `SAVEPOINT` queries.

    This is how the script should work.

    At t=0, `run_atomic_transactions` and `run_savepoints` starts almost together
    and they both read the same `count` value from `count` row with `bucket` id `1`.
    In this case, count is 203.

    At t=1, `run_atomic_transactions` updates `count` field.

    At t=1.5, `run_savepoints` reads `count` for `bucket` id 1, and still sees the
    initial count value, i.e., 203, indicating that there was no dirty read.

    At t=2, `run_atomic_transactions` successfully commits the atomic transaction
    and sets count to 200

    At t=2.5, `run_savepoints` reads count for bucket_id 1, and sees the
    newly committed value by `run_atomic_transactions`, which is 200. It then
    goes ahead and updates the count value to 1. It then enters the inner
    transaction block and increment count value by 1, which means count becomes
    2. Since count is even, it gets committed in the inner transaction block
    (if count were odd, it would have been rollbacked to value set by
    the outer transaction). Please not that the outer block transaction has
    not yet been committed.

    At t=3, `run_atomic_transactions` reads count for bucket_id 1 and
    sees the value it had committed, 200.

    At t=3.5, `run_savepoints` exits the outer transaction block by setting
    count to 2.

    At t=4, the next loop starts for both `run_atomic_transactions` and `run_savepoints`
    where they both start with count set to 2.
    """

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
