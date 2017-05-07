import csv
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Sequence, Dict, Optional, Tuple

import abc
import hashlib
import re
from contracts import contract
from moneyed import Money, get_currency
from pytz import timezone
from scrooge.models import Transaction, Account


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
                yield self.convert_row(row)

    @contract
    def convert_row(self, row: Sequence[str]) -> Transaction:
        # CSV format documentation is available at
        # https://www.rabobank.nl/images/formaatbeschrijving_csv_kommagescheiden_nieuw_29539176.pdf.
        # The colums are:
        # 0)  IBAN of own bank account. Required.
        # 1)  ISO 4217 currency code.
        # 2)  Interest date. ^\d{6}$ (YYYYMMDD).
        # 3)  "D" for debit and "C" for credit transactions respectively.
        # 4)  Two-decimal amount, with a period as decimal separator. Max 14
        #     characters.
        # 5)  Number of the remote bank account. Optional. Max 35 characters.
        # 6)  Remote name. Max 70 characters.
        # 7)  Transaction date. ^\d{6}$ (YYYYMMDD).
        # 8)  Booking code. 2 characters.
        # 9) Filler. Max 6 characters.
        # 10) Description, line 1. Max 35 characters.
        # 11) Description, line 2. Max 35 characters.
        # 12) Description, line 3. Max 35 characters.
        # 13) Description, line 4. Max 35 characters.
        # 14) Description, line 5. Max 35 characters.
        # 15) Description, line 6. Max 35 characters.
        # 16) SEPA credit transfer end-to-end ID. Max 35 characters.
        # 17) SEPA credit transfer remove account ID. Max 35 characters.
        # 18) SEPA direct debit mandate ID. Max 35 characters.

        remote_id = 'rabobank-csv:' + hashlib.sha256(
            "\n".join(row).encode('utf-8')).hexdigest()
        try:
            transaction = Transaction.objects.get(remote_id=remote_id)
        except Transaction.DoesNotExist:
            transaction = Transaction(remote_id=remote_id)

        # @todo Import the following columns: 8, 16, 17, 18. Design a way to
        #  set transaction types (POS, ATM, wire transfer, direct debit,
        # ...) In other words: through which medium was the transaction made?
        # ''  : ?
        # 'gb': Non-euro ATM?
        # 'tb': ?
        # 'sb': Maybe incoming SEPA wire transfer?
        # 'ga': ATM, domestic and foreign. Seems like EUR only.
        # 'bg': Wire transfers, including scheduled ones. Includes SEPA
        #       debit transfers.
        # 'db': Charges imposed by the bank?
        # 'id': iDEAL
        # 'ac': Acceptgiro
        # 'cb': "Creditbetaling"?. Several wire incoming wire transfers with
        #       opposing IBANs available.
        # 'bc': ?
        # 'ei': "Euro-incasso"? Always has the last SEPA fields. Direct debit.
        # 'ba': "Betaalautomaat"? Looks like PoS terminals worldwide.

        # Set the description early, because we need to analyze it later.
        transaction.description = ' '.join(
            [row[10], row[11], row[12], row[13], row[14], row[15]]).strip()

        # Set the original transaction date.
        year = int(row[7][0:4])
        month = int(row[7][4:6])
        day = int(row[7][6:8])
        # Because Rabobank does not include times, try and find them in the
        # description (hh:mm or hh:mm:ss). Otherwise, default to midnight.
        hour = 0
        minute = 0
        second = 0
        time_zone = timezone('Europe/Amsterdam')
        description_time = self._get_time(transaction.description)
        if description_time is not None:
            hour, minute, second = description_time
        transaction.remote_date = time_zone.localize(
            datetime(year, month=month,
                     day=day,
                     hour=hour, minute=minute,
                     second=second))

        # Set account information.
        own_account, own_account_created = Account.objects.get_or_create(
            number=row[0])
        transaction.own_account = own_account
        transaction.opposing_account_number = row[5]
        transaction.opposing_name = row[6]

        # Set the amount.
        amount = Decimal(row[4])
        if 'D' == row[3]:
            amount *= -1
        transaction.amount = Money(amount, get_currency(row[1]))

        return transaction

    @staticmethod
    def _get_time(haystack: str) -> Optional[Tuple[int, int, int]]:
        # Find times (hh:mm or hh:mm:ss).
        times = re.findall(
            '(?<![\d:])(\d\d:\d\d(:\d\d)?)(?![\d:])',
            haystack)

        # If there is more or less than 1 time, don't use anything as we
        # cannot be certain.
        if 1 != len(times):
            return None

        time, _ = times[0]
        time_parts = time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        if 3 == len(time_parts):
            second = int(time_parts[2])
        else:
            second = 0
        # This data may represent an invalid time, but that can only be
        # reliably validated in the context of a specific date and time zone.
        return hour, minute, second


@contract
def get_parsers() -> Dict[str, Parser]:
    return {
        "rabobank-csv": RabobankCsvParser(),
    }


@contract
def get_parser(format: str) -> Parser:
    parsers = get_parsers()
    if format not in parsers:
        raise ValueError('%s is an unknown format. Known formats are %s.' % (
            format, ', '.join(parsers.keys())))
    return parsers[format]
