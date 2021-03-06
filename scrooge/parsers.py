import csv
from decimal import Decimal
from typing import Iterable, Sequence, Dict, Optional

import abc
import hashlib
from contracts import contract
from moneyed import Money, get_currency
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
                transaction = self.convert_row(row)
                if transaction is not None:
                    yield transaction

    # @todo Enforcing types through the contract() annotation causes an
    #   error to be raised during the check.
    # @contract
    def convert_row(self, row: Sequence[str]) -> Optional[Transaction]:
        # CSV format documentation is available at
        # https://www.rabobank.nl/images/formaatbeschrijving_csv_kommagescheiden_nieuw_29539176.pdf.
        # The colums are:
        # 1)  IBAN of own bank account. Required.
        # 2)  ISO 4217 currency code.
        # 3)  Interest date. ^\d{6}$ (YYYYMMDD).
        # 4)  "D" for debit and "C" for credit transactions respectively.
        # 5)  Two-decimal amount, with a period as decimal separator. Max 14
        #     characters.
        # 6)  Number of the remote bank account. Optional. Max 35 characters.
        # 7)  Remote name. Max 70 characters.
        # 8)  Transaction date. ^\d{6}$ (YYYYMMDD).
        # 9)  Booking code. 2 characters.
        # 10) Filler. Max 6 characters.
        # 11) Description, line 1. Max 35 characters.
        # 12) Description, line 2. Max 35 characters.
        # 13) Description, line 3. Max 35 characters.
        # 14) Description, line 4. Max 35 characters.
        # 15) Description, line 5. Max 35 characters.
        # 16) Description, line 6. Max 35 characters.
        # 17) SEPA credit transfer end-to-end ID. Max 35 characters.
        # 18) SEPA credit transfer remove account ID. Max 35 characters.
        # 19) SEPA direct debit mandate ID. Max 35 characters.

        remote_id = 'rabobank-csv:' + hashlib.sha256(
            "\n".join(row).encode('utf-8')).hexdigest()

        if Transaction.objects.filter(remote_id=remote_id).exists():
            return None

        transaction = Transaction()
        transaction.remote_id = remote_id
        try:
            own_account = Account.objects.get(number=row[0])
        except Account.DoesNotExist:
            own_account = Account(number=row[0], label=row[0])
            own_account.save()
        transaction.own_account = own_account
        transaction.opposing_name = row[6]
        transaction.amount = Money(Decimal(row[4]), get_currency(row[1]))
        transaction.description = ' '.join(
            [row[10], row[11], row[12], row[13], row[14], row[15]]).strip()
        return transaction


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
