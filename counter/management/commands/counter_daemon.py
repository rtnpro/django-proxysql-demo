from django.core.management.base import BaseCommand

from counter.counter_daemon import CounterDaemon


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            dest='workers',
            default=10,
            type=int,
            help='Number of multiprocess workers to run.')
        parser.add_argument(
            '--max-tasks',
            dest='max_tasks',
            default=100,
            type=int,
            help='Max tasks run per process.')
        parser.add_argument(
            '--poll-interval',
            dest='poll_interval',
            default=None,
            type=float,
            help='Poll interval.')
        parser.add_argument(
            '--task-timeout',
            dest='task_timeout',
            default=0.1,
            type=float,
            help='Timeout period for a task.')
        parser.add_argument(
            '--task-default-sleep',
            dest='task_default_sleep',
            default=0.01,
            type=float,
            help='Default sleep for a task.')
        parser.add_argument(
            '--task-sleep-rand-range_limit',
            dest='task_sleep_rand_range_limit',
            default=20,
            type=int,
            help='Random range to pick a value from to multiply with --task-default-sleep to calculate sleep period for a task.')

    def handle(self, *args, **options):
        daemon = CounterDaemon(
            workers=options['workers'],
            poll_interval=options['poll_interval'],
            max_tasks=options['max_tasks'],
            task_timeout=options['task_timeout'],
            task_default_sleep=options['task_default_sleep'],
            task_sleep_rand_range=(1, options['task_sleep_rand_range_limit'])
        )
        daemon.start()
