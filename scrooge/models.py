from django.db import models
from django_iban.fields import IBANField
from djmoney.models.fields import MoneyField


class Account(models.Model):
    number = IBANField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default='')


class Transaction(models.Model):
    # The account under which to log this transaction.
    own_account = models.ForeignKey(Account, on_delete=models.PROTECT,
                                    related_name='origin_account_number')
    # The optional account from which the transaction came, or to which it
    #  went.
    remote_account_number = models.CharField(max_length=35, default='',
                                             blank=True)
    amount = MoneyField(max_digits=10, decimal_places=3)
