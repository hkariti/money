import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Account, Transaction, Category
from .serializers import AccountSerializer, TransactionSerializer, CategorySerializer
import fetch_leumicard
import fetch_leumi

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
def fetch_leumicard_view(request):
    try:
        user = request.data["user"]
        passwd = request.data["pass"]
        month = int(request.data.get("month", datetime.date.today().month))
        year = int(request.data.get("year", datetime.date.today().year))
    except IndexError:
        return Response("'user' and 'pass' params are required.", status=400)
    try:
        s = fetch_leumicard.login(user, passwd)
        cc_transactions = fetch_leumicard.get_month_transactions(s, month, year)
        transactions = [ TransactionSerializer(Transaction.from_credit_card(t)).data for t in cc_transactions ]
        return Response(transactions)
    except fetch_leumicard.FetchException as e:
        return Response(e.message, status=400)

@api_view(http_method_names=['POST'])
def fetch_leumi_view(request):
    try:
        user = request.data["user"]
        passwd = request.data["pass"]
        month = int(request.data.get("month", datetime.date.today().month))
        year = int(request.data.get("year", datetime.date.today().year))
    except IndexError:
        return Response("'user' and 'pass' params are required.", status=400)
    try:
        s = fetch_leumi.login(user, passwd)
        transactions = fetch_leumi.get_month_transactions(s, month, year)
        serialized_transactions = [ TransactionSerializer(t).data for t in transactions ]
        return Response(serialized_transactions)
    except fetch_leumi.FetchException as e:
        return Response(e.message, status=400)
    except Exception as e:
        return Response(e.message, status=500)
