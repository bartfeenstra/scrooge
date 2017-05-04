from typing import Sequence

import abc
import re
from contracts import contract
from scrooge.models import Transaction, Tag


class Processor(object):
    @abc.abstractmethod
    @contract
    def process(self, transaction: Transaction):
        """
        Processes a transaction.
        """
        pass


class TaggingProcessor(Processor):
    @contract
    def add_tag(self, transaction: Transaction, tag_name: str):
        tag, tag_created = Tag.objects.get_or_create(name=tag_name)
        transaction.tags.add(tag)


class AlbertHeijn(TaggingProcessor):
    @contract
    def process(self, transaction: Transaction):
        if transaction.tags.filter(name='pos').exists():
            needles = [
                'ALBERT HEIJN \d+ [A-Z]+',
                'AH to go',
            ]
            for needle in needles:
                if re.fullmatch('^.*%s.*$' % needle, transaction.description,
                                re.I) is not None:
                    self.add_tag(transaction, 'albert-heijn')


class Atm(TaggingProcessor):
    @contract
    def process(self, transaction: Transaction):
        # @todo Maybe this can be done through the "ga" Rabobank CSV
        #  transaction type.
        if re.fullmatch('^.*Geldautomaat \d\d:\d\d pasnr. \d\d\d.*$',
                        transaction.description) is not None:
            self.add_tag(transaction, 'atm')


class Pos(TaggingProcessor):
    @contract
    def process(self, transaction: Transaction):
        # @todo Maybe this can be done through the "ba" Rabobank CSV
        #  transaction type.
        if re.fullmatch('^.*Betaalautomaat \d\d:\d\d pasnr. \d\d\d.*$',
                        transaction.description) is not None:
            self.add_tag(transaction, 'pos')


@contract
def get_processors() -> Sequence[Processor]:
    return [
        Atm(),
        Pos(),
        AlbertHeijn(),
    ]
