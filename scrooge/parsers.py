import abc
from contracts import contract
from scrooge.models import Transaction
import csv
from typing import Iterable, Sequence


class Parser(object):

    @abc.abstractmethod
    @contract
    def parse(self, source: str) -> Iterable[Transaction]:
        """
        Parses the resource to transactions.
        """
        pass


class RabobankCsvParser(Parser):

    @contract
    def parse(self, source: str) -> Iterable[Transaction]:
        with open(source, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                yield self._convert(row)

    @contract
    def _convert(self, row: Sequence[str]) -> Transaction:
        transaction = Transaction()
        transaction.currency_code = row[1]
        return transaction



@contract
def get_parsers() -> dict:
    return {
        "rabobank-csv": RabobankCsvParser(),
    }


@contract
def get_parser(format: str) -> Parser:
    parsers = get_parsers()
    if format not in parsers:
        raise ValueError('%s is an unknown format. Known formats are %s.' % (format, ', '.join(parsers.keys())))
    return parsers[format]