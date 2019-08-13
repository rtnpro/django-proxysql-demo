import logging
import time

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from pebble import ProcessPool

from counter.models import Counter

logger = logging.getLogger('counter')

def run_long_atomic_transactions(name, bucket_id, trials=1):
    for i in range(1, (1 + trials)):
        connections.close_all()
        try:
            with transaction.atomic():
                bucket = Counter.objects.get(bucket=bucket_id)
                initial_count = bucket.count

                transaction_type = 'outer'

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    'enter',  # event
                    initial_count)
                time.sleep(1.5)

                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                time.sleep(1)

                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                bucket.count = i
                bucket.save()
                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)

                # try:
                #     with transaction.atomic():
                transaction_type = 'inner'
                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    'enter',  # event
                    bucket.count)

                if bucket.count != i:
                    logger.error(
                        '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                        name,
                        i,
                        transaction_type,
                        'expected: %s' % i,  # event
                        'Got: %s' % bucket.count)

                bucket.count = i + 1
                bucket.save()

                bucket = Counter.objects.get(bucket=bucket_id)

                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    'save',  # event
                    bucket.count)

                if bucket.count != (i + 1):
                    logger.error(
                        '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                        name,
                        i,
                        transaction_type,
                        'expected: %s' % i + 1,  # event
                        'Got: %s' % bucket.count)


                if bucket.count % 2 != 0:
                    bucket.count -= 1
                    bucket.save()
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    'exit',  # event
                    bucket.count)
                transaction_type = 'outer'

                time.sleep(1)

                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    '',  # event
                    bucket.count)
                if bucket.count != (i + 1 * (i % 2)):
                    logger.error(
                        '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                        name,
                        i,
                        transaction_type,
                        'expected: %s' % (i + (1 * (i % 2))),  # event
                        'Got: %s' % bucket.count)
                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
                    name,
                    i,
                    transaction_type,
                    'exit',  # event
                    bucket.count)
        except Exception as e:
            logger.exception(e)
        time.sleep(0.5)


def run_atomic_transactions(name, bucket_id, trials=1):
    for i in range(200, (200 + trials)):
        connections.close_all()
        try:
            with transaction.atomic():
                transaction_type = 'main'
                bucket = Counter.objects.get(bucket=bucket_id)
                logger.info(
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
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
                    '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
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
            '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
            name,
            i,
            transaction_type,
            'exit',  # event
            bucket.count)
        time.sleep(1)

        bucket = Counter.objects.get(bucket=bucket_id)
        logger.info(
            '%-8s\t%-8s\t%-8s\t%-8s\t%-8s',
            name,
            i,
            transaction_type,
            '',  # event
            bucket.count)

        time.sleep(1)

class Command(BaseCommand):
    """
    This command tests running two processes in parallel running transactions.
    `run_atomic_transactions` or `T1` runs plain `atomic` transactions and
    `run_savepoints` or `T2` runs nested `atomic` transactions which internally uses
    `SAVEPOINT` queries.

    This is how the script should work.

    At t=0, `T1` and `T2` starts almost together
    and they both read the same `count` value from `count` row with `bucket` id `1`.
    In this case, count is `0`

    At t=1, `T1` updates `count` field.

    At t=1.5, `T2` reads `count` for `bucket` id 1. It will see different values
    of count based on what tx_isolation is used.

    - `read-uncommitted`: 200
    - `read-committed`: 0
    - `repeatable-read`: 0

    At t=2, `T1` successfully commits the atomic transaction
    and sets count to 200.

    At t=2.5, `T2` reads count for bucket_id 1, and sees the
    newly committed value by `T1`, which is 200. It then
    goes ahead and updates the count value to 1. It then enters the inner
    transaction block and increment count value by 1, which means count becomes
    2. Since count is even, it gets committed in the inner transaction block
    (if count were odd, it would have been rollbacked to value set by
    the outer transaction). Please not that the outer block transaction has
    not yet been committed.

    At t=3, `T1` reads count for bucket_id 1 sees the following values of count for different tx_isolation levels:

    - `read-uncommitted`: 2
    - `read-committed`: 200
    - `repeatable-read`: 200

    At t=3.5, `T2` exits the outer transaction block by setting count to 2.

    At t=4, next iteration for both processes start.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket',
            dest='bucket',
            default=1,
            type=int,
            help='Counter bucket against which to run tests.')
        parser.add_argument(
            '--trials',
            dest='trials',
            default=1,
            type=int,
            help='Number of test trials.')


    def handle(self, *args, **options):
        trials = options['trials']
        bucket_id = options['bucket']

        pool = ProcessPool(max_workers=2)
        pool._start_pool()

        bucket, _ = Counter.objects.get_or_create(bucket=bucket_id)
        bucket.count = 0
        bucket.save()

        future_1 = pool.schedule(
            run_atomic_transactions,
            args=('T1', bucket_id, trials)
        )
        future_2 = pool.schedule(
            run_long_atomic_transactions,
            args=('T2', bucket_id, trials)
        )
        pool.close()
        pool.join()
