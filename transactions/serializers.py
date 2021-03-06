from .models import Account, Category, Transaction, Pattern
from rest_framework import serializers
from django.db.models import Q, CheckConstraint
from rest_framework.validators import UniqueTogetherValidator

from .auto_category import verify_rule


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'backend_id', 'backend_type']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']


class PatternSerializer(serializers.ModelSerializer):
    matcher = serializers.JSONField()
    target_category = serializers.SlugRelatedField(slug_field='title', queryset=Category.objects.all(), allow_null=False)
    class Meta:
        model = Pattern
        fields = ['id', 'name', 'matcher', 'target_category', 'enabled']
    def validate(self, data):
        try:
            verify_rule(data['matcher'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='title', queryset=Category.objects.all(), allow_null=True)
    from_account = serializers.SlugRelatedField(slug_field='name', queryset=Account.objects.all(), allow_null=True)
    to_account = serializers.SlugRelatedField(slug_field='name', queryset=Account.objects.all(), allow_null=True)

    # Yes, this validators are an exact copy of the ones in the Model. This is a design choice of DRF to separate
    # validation and the model. I think that's stupid, at least for my case, but their validation errors are nice.
    def validate(self, data):
        if not data['from_account'] and not data['to_account']:
            raise serializers.ValidationError("At least one of from_account or to_account must not be null")
        return data
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_date', 'bill_date', 'from_account', 'to_account', 'transaction_amount', 'description', 'category', 'original_currency', 'billed_amount', 'confirmation', 'notes']
        validators = [
            UniqueTogetherValidator(fields=['transaction_date', 'from_account', 'to_account', 'billed_amount', 'description'],
                             queryset=Transaction.objects.all()),
            UniqueTogetherValidator(fields=['transaction_date', 'to_account', 'billed_amount', 'description'],
                             queryset=Transaction.objects.filter(from_account=None)),
            UniqueTogetherValidator(fields=['transaction_date', 'from_account', 'billed_amount', 'description'],
                             queryset=Transaction.objects.filter(to_account=None))
        ]
