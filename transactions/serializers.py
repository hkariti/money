from .models import Account, Category, Transaction
from rest_framework import serializers


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'backend_id', 'backend_type']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TransactionSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if not data['from_account'] and not data['to_account']:
            raise serializers.ValidationError("At least one of from_account or to_account must not be null")
        return data
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_date', 'bill_date', 'from_account', 'to_account', 'transaction_amount', 'description', 'category', 'original_currency', 'billed_amount', 'confirmation', 'notes']
