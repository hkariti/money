import time
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv
from .models import Account, Transaction, Category
from .serializers import AccountSerializer, TransactionSerializer, CategorySerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (csv.CSVRenderer, )

    def get_queryset(self):
        from_bill_arg = self.request.query_params.get('from_bill', [''])[0]
        to_bill_arg = self.request.query_params.get('to_bill', [''])[0]
        if not from_bill_arg:
            from_bill = None
        else:
            from_bill = time.strptime(from_bill_arg, '%d/%m/%y')
        if not to_bill_arg:
            to_bill = None
        else:
            to_bill = time.strptime(from_bill_arg, '%d/%m/%y')

        return Transaction.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
