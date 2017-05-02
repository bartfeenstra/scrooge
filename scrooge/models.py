from django.core.exceptions import ValidationError
from django.db import models
from django_iban.fields import IBANField
import re


def validate_currency_code(value: str):
    if re.match('^[A-Z]{3}$', value) is None:
        raise ValidationError('%s is not a valid ISO 4217 currency code.' % value)


class Transaction(models.Model):
    # @todo Find out IBAN specs and add validation.
    origin_account_number = IBANField(max_length=34)
    recipient_account_number = IBANField(max_length=34)
    currency_code = models.CharField(max_length=3, validators=[validate_currency_code])