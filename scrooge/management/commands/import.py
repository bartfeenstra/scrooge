import time

import os
from contracts import contract
from django.core.management.base import BaseCommand
from scrooge.parsers import get_parser
from scrooge.processors import get_processors


@contract()
def get_source(source: str) -> str:
    # Confirm the source exists.
    if not os.path.isfile(source):
        raise OSError('Source %s does not exist.' % source)

    # Get the real path for readability.
    source = os.path.realpath(source)

    return source


class Command(BaseCommand):
    help = 'Imports bank statements.'

    def add_arguments(self, parser):
        parser.add_argument('format', nargs=1, type=get_parser)
        parser.add_argument('source', nargs=1, type=get_source)

    def handle(self, *args, **options):
        source = options['source'][0]
        parser = options['format'][0]
        processors = get_processors()

        transactions = parser.parse(source)

        count = 0
        start_time = time.time()
        timer = start_time
        for transaction in transactions:
            # Save the transaction, so processors have a primary key to work
            # with.
            transaction.save()
            for processor in processors:
                processor.process(transaction)
            # Save any changes the processors made.
            transaction.save()
            count += 1
            if time.time() - 1 > timer:
                timer = time.time()
                self._log(count, start_time)
        self._log(count, start_time)

    @contract
    def _log(self, count: int, start_time: float):
        self.stdout.write(
            self.style.SUCCESS(
                'Imported %d new transaction(s) in %d second(s).' % (
                    count, time.time() - start_time)))
