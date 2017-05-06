from django.db import models
from django_iban.fields import IBANField
from djmoney.models.fields import MoneyField


class Account(models.Model):
    number = IBANField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default='')


class Tag(models.Model):
    name = models.CharField(max_length=255, primary_key=True)


class Transaction(models.Model):
    # The ID of the original, remote transaction.
    remote_id = models.CharField(max_length=255, unique=True)
    # The date-time the original, remote transaction was made.
    remote_date = models.DateTimeField()
    # The date-time the transaction was created.
    created = models.DateTimeField(auto_now_add=True)
    # The date-time the transaction was last updated.
    update = models.DateTimeField(auto_now=True)
    # The account under which to log this transaction.
    own_account = models.ForeignKey(Account, on_delete=models.PROTECT,
                                    related_name='origin_account_number')
    # The optional account from which the transaction came, or to which it
    #  went.
    opposing_account_number = models.CharField(max_length=255, default='',
                                               blank=True)
    opposing_name = models.CharField(max_length=255, default='', blank=True)
    amount = MoneyField(max_digits=10, decimal_places=3)
    tags = models.ManyToManyField(Tag)
    description = models.CharField(max_length=255, default='', blank=True)
