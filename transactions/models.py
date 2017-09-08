from django.db import models

class Accounts(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Categories(models.Model):
    title = models.CharField(max_length=100, unique=True)

class Subcategories(models.Model):
    title = models.CharField(max_length=100, unique=True)

class Transactions(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="transactions_from")
    to_account = models.ForeignKey(Accounts, on_delete=models.PROTECT, related_name="transactions_to")
    amount = models.DecimalField(max_digits=9, decimal_places=3)
    category = models.ForeignKey(Categories, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(Subcategories, on_delete=models.PROTECT)
    original_current = models.CharField(max_length=3)
    amount_original = models.DecimalField(max_digits=9, decimal_places=3)
    confirmation = models.IntegerField()
    notes = models.CharField(max_length=200)
    class Meta:
        unique_together = (('date', 'from_account', 'to_account', 'amount'),)

