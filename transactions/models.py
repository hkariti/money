import datetime
from django.db import models
from django.core.exceptions import ValidationError


class Accounts(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Categories(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class Subcategories(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class ClusteringRules(models.Model):
    TYPE_EXACT = 0
    TYPE_REGEX = 1
    TYPE_COICES = ((TYPE_EXACT, 'exact'), (TYPE_REGEX, 'regex'))
    match = models.CharField(max_length=100, unique=True)
    type = models.IntegerField(choices=TYPE_COICES, default=TYPE_EXACT, blank=False)
    category = models.ForeignKey(Categories, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(Subcategories, on_delete=models.PROTECT, blank=True, null=True)

class Transactions(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="transactions_from", blank=True, default=0)
    to_account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="transactions_to", blank=True, default=0)
    amount = models.DecimalField(max_digits=9, decimal_places=3)
    description = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Categories, on_delete=models.PROTECT, blank=True, null=True)
    subcategory = models.ForeignKey(Subcategories, on_delete=models.PROTECT, blank=True, null=True)
    original_currency = models.CharField(max_length=3, blank=True, null=True)
    amount_original = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    confirmation = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return "{0} from {1} to {2} on {3}".format(amount, from_account.name, to_account.name, date.ctime())

    def clean(self):
        if not self.from_account and not self.to_account:
            raise ValidationError("At least one of from_account,to_account is required.")

    class Meta:
        unique_together = (('date', 'from_account', 'to_account', 'amount', 'description'),)

