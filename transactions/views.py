import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Account, Transaction, Category
from .serializers import AccountSerializer, TransactionSerializer, CategorySerializer

import fetchers

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@api_view(http_method_names=['POST'])
def fetch_view(request, backend):
    try:
        backend_obj = fetchers.get_backend(backend)
    except KeyError:
        return Response(f'Unknown backend: {backend}', status=404)
    try:
        user = request.data["user"]
        passwd = request.data["pass"]
        month = int(request.data.get("month", datetime.date.today().month))
        year = int(request.data.get("year", datetime.date.today().year))
        accounts = list(Account.objects.filter(backend_type=backend))
    except KeyError as e:
        return Response("'user' and 'pass' params are required", status=400)
    except ValueError:
        return Response("'month' and 'year' must be integers", status=400)
    except Exception as e:
        return Response(f'Error: {e}', status=500)
    try:
        s = backend_obj.login(user, passwd)
        transactions = backend_obj.get_month_transactions(s, month, year, accounts)
        serialized_transactions = [ TransactionSerializer(t).data for t in transactions ]
        return Response(serialized_transactions)
    except fetchers.FetchException as e:
        return Response(str(e), status=400)
