import datetime
from django.db import models
from django.core.exceptions import ValidationError

import funcy

class Account(models.Model):
    name = models.CharField(max_length=100, unique=True)
    backend_id = models.CharField(max_length=100)
    backend_type = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

    class Meta:
        unique_together = (('backend_id', 'backend_type'),)

class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    def natural_key(self):
        return self.title

class Transaction(models.Model):
    transaction_date = models.DateField()
    bill_date = models.DateField()
    from_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions_from", null=True, blank=True, default=None)
    to_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions_to", null=True, blank=True, default=None)
    transaction_amount = models.DecimalField(max_digits=9, decimal_places=3)
    description = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True)
    original_currency = models.CharField(max_length=3, blank=True, null=True)
    billed_amount = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    confirmation = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        from_name = getattr(self.from_account, 'name', 'outside')
        to_name = getattr(self.to_account, 'name', 'outside')
        return "{0} from {1} to {2} on {3}".format(self.billed_amount, from_name, to_name, self.transaction_date.ctime())

    def clean(self):
        if not self.from_account and not self.to_account:
            raise ValidationError("At least one of from_account,to_account is required.")

    class Meta:
        unique_together = (('transaction_date', 'from_account', 'to_account', 'billed_amount', 'description'),)

