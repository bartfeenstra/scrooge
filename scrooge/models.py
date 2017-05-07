import rules
from contracts import contract
from django.core.exceptions import PermissionDenied
from django.db import models
from django_iban.fields import IBANField
from djmoney.models.fields import MoneyField


class Account(models.Model):
    number = IBANField(primary_key=True)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label


class Tag(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label


class Transaction(models.Model):
    # Programatically imported transactions can use this field to map
    # transactions to data in remote systems. Any non-empty value means the
    # transaction MUST NOT be editable outside its importer.
    remote_id = models.CharField(max_length=255, unique=True, default='',
                                 editable=False)
    # The account under which to log this transaction.
    own_account = models.ForeignKey(Account, on_delete=models.PROTECT)
    # The optional account from which the transaction came, or to which it
    #  went.
    opposing_account_number = models.CharField(max_length=255, default='',
                                               blank=True)
    opposing_name = models.CharField(max_length=255, default='', blank=True)
    amount = MoneyField(max_digits=10, decimal_places=3,
                        default_currency='EUR')
    tags = models.ManyToManyField(Tag)
    description = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return self.description

    def is_editable(self):
        return self.remote_id == ''


@contract
def rule_transaction_is_editable(permission: str):
    def transaction_is_editable(user, transaction):
        if transaction is None:
            # Returning false gives the other back-ends a chance to decide.
            return False
        if transaction.is_editable():
            # Perform the permission check again, but without an object,
            # so other back-ends get a chance to decide.
            return user.has_perm(permission)
        # The transaction is not editable.
        raise PermissionDenied()

    return transaction_is_editable


rules.add_perm('scrooge.change_transaction',
               rule_transaction_is_editable('scrooge.change_transaction'))
rules.add_perm('scrooge.delete_transaction',
               rule_transaction_is_editable('scrooge.change_transaction'))
