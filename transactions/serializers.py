from .models import Account, AuthSource, Category, Transaction, Pattern
from rest_framework import serializers
from django.db.models import Q, CheckConstraint
from rest_framework.validators import UniqueTogetherValidator
from .validators import validate_account_schema, validate_auth_source_schema, SchemaError
from .auto_category import verify_rule


class AuthSourceSerializer(serializers.ModelSerializer):
    settings = serializers.JSONField(allow_null=True)
    class Meta:
        model = AuthSource
        fields = ['id', 'name', 'auth_type', 'settings']

    def validate(self, data):
        if data['settings'] is None:
            return
        try:
            validate_auth_source_schema(data['auth_type'], data['settings'])
        except KeyError:
            raise serializers.ValidationError(f"{data['auth_type']}: Bad auth type value")
        except SchemaError as e:
            raise serializers.ValidationError(f'settings field failed JSON schema check: {e.message}')

        return data

class AccountSerializer(serializers.ModelSerializer):
    settings = serializers.JSONField(allow_null=True)
    auth_source_name = serializers.SlugRelatedField(slug_field='name', queryset=AuthSource.objects.all(), allow_null=True)

    class Meta:
        model = Account
        fields = ['id', 'name', 'backend_id', 'backend_type', 'settings', 'auth_source_name', 'auth_source_item_id']


    def validate(self, data):
        if data['settings'] is not None:
            try:
                validate_account_schema(data['backend_type'], data['settings'])
            except KeyError:
                raise serializers.ValidationError(f"{data['backend_type']}: Bad backend type")
            except SchemaError as e:
                raise serializers.ValidationError(f'settings field failed JSON schema check: {e.message}')
        if data['auth_source_name'] is None and data['auth_source_item_id'] is not None:
                raise serializers.ValidationError(f'auth_source_item_id can not be null if auth_source_name is null')

        return data


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


class NonAtomicListSerializer(serializers.ListSerializer):
    """
    A serializer that writes bulk-data non atomically. This is to skip over objects that could not be written.
    """
    def create(self, validated_data):
        written = []
        errors = []
        for t in validated_data:
            try:
                written.append(self.child.create(t))
                errors.append({})
            except serializers.ValidationError as e:
                errors.append(e.detail)
        self.create_errors = errors
        return written


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='title', queryset=Category.objects.all(), allow_null=True)
    from_account = serializers.SlugRelatedField(slug_field='name', queryset=Account.objects.all(), allow_null=True)
    to_account = serializers.SlugRelatedField(slug_field='name', queryset=Account.objects.all(), allow_null=True)

    def create(self, validated_data):
       try:
           return Transaction.objects.create(**validated_data)
       except Exception as e:
           raise serializers.ValidationError(dict(create=str(e)))
    # Yes, this validator are an exact copy of the one in the Model. This is a design choice of DRF to separate
    # validation and the model. I think that's stupid, at least for my case, but their validation errors are nice.
    def validate(self, data):
        if not data['from_account'] and not data['to_account']:
            raise serializers.ValidationError("At least one of from_account or to_account must not be null")
        return data
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_date', 'bill_date', 'from_account', 'to_account', 'transaction_amount', 'description', 'category', 'original_currency', 'billed_amount', 'confirmation', 'notes']

        list_serializer_class = NonAtomicListSerializer
