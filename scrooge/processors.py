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
    def add_tag(self, transaction: Transaction, tag_name: str, tag_label:
                str = ''):
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        if tag.label == '':
            tag.label = tag_label
            tag.save()
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
                    self.add_tag(transaction, 'albert-heijn', 'Albert Heijn')


class Atm(TaggingProcessor):
    @contract
    def process(self, transaction: Transaction):
        # @todo Maybe this can be done through the "ga" Rabobank CSV
        #  transaction type.
        if re.fullmatch('^.*Geldautomaat \d\d:\d\d pasnr. \d\d\d.*$',
                        transaction.description) is not None:
            self.add_tag(transaction, 'atm', 'ATM')


class Pos(TaggingProcessor):
    @contract
    def process(self, transaction: Transaction):
        # @todo Maybe this can be done through the "ba" Rabobank CSV
        #  transaction type.
        if re.fullmatch('^.*Betaalautomaat \d\d:\d\d pasnr. \d\d\d.*$',
                        transaction.description) is not None:
            self.add_tag(transaction, 'pos', 'Point of Sale')


@contract
def get_processors() -> Sequence[Processor]:
    return [
        Atm(),
        Pos(),
        AlbertHeijn(),
    ]
