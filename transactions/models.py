import datetime
from django.db import models
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint
from django.core.exceptions import ValidationError
import jsonfield

class AuthSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    auth_type = models.CharField(max_length=100)
    settings = jsonfield.JSONField(null=True, validators=[])

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

class Account(models.Model):
    name = models.CharField(max_length=100, unique=True)
    backend_id = models.CharField(max_length=100)
    backend_type = models.CharField(max_length=100)
    settings = jsonfield.JSONField(null=True, validators=[])
    auth_source_name = models.ForeignKey(AuthSource, on_delete=models.PROTECT, null=True, blank=True)
    auth_source_item_id = models.CharField(null=True, max_length=100)

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

class Pattern(models.Model):
    name = models.CharField(max_length=10, default='', unique=True)
    matcher = jsonfield.JSONField()
    target_category = models.ForeignKey(Category, on_delete=models.PROTECT, null=False, blank=False)
    enabled = models.BooleanField(default=False)

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

    class Meta:
        constraints = [
            UniqueConstraint(fields=['transaction_date', 'from_account', 'to_account', 'billed_amount', 'description'],
                             name='unique_transfer'),
            UniqueConstraint(fields=['transaction_date', 'to_account', 'billed_amount', 'description'],
                             condition=Q(from_account=None),
                             name='unique_income'),
            UniqueConstraint(fields=['transaction_date', 'from_account', 'billed_amount', 'description'],
                             condition=Q(to_account=None),
                             name='unique_expense'),
            models.CheckConstraint(
                check=Q(from_account__isnull=False) | Q(to_account__isnull=False),
                name='some_account_not_null'
            )
        ]
