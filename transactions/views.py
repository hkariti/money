import datetime
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from .models import Account, Transaction, Category, Pattern
from .serializers import AccountSerializer, TransactionSerializer, CategorySerializer, PatternSerializer

import fetchers
from .auto_category import categorize

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PatternViewSet(viewsets.ModelViewSet):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        if 'year' in self.kwargs:
            queryset = queryset.filter(transaction_date__year=self.kwargs['year'])
        if 'month' in self.kwargs:
            queryset = queryset.filter(transaction_date__month=self.kwargs['month'])
        if 'day' in self.kwargs:
            queryset = queryset.filter(transaction_date__day=self.kwargs['day'])

        return queryset.all()

    @action(detail=False, url_path='by_date/(?P<year>[0-9]+)(/(?P<month>[0-9]+)(/(?P<day>[0-9]))?)?')
    def list_by_date(self, request, *args, **kwargs):
        return self.list(request)

    def create(self, request, *args, **kwargs):
        bulk_data = request.data if isinstance(request.data, list) else [request.data]
        serializer = self.get_serializer(data=bulk_data, many=True)
        if serializer.is_valid(raise_exception=False):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            written = []
            errors = {}
            for i, e in enumerate(serializer.create_errors):
                if e:
                    errors[i] = e
                else:
                    written.append(serializer.data[i])
            if errors:
                message="partial_write"
            else:
                message="ok"
            return Response(dict(message=message, written=written, errors=errors), status=status.HTTP_201_CREATED)
        else:
            errors = { i: e for i, e in enumerate(serializer.errors) if e }
            return Response(dict(message="failed_validation", errors=errors), status=status.HTTP_400_BAD_REQUEST)

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
        auto_category_rules = list(Pattern.objects.all())
    except KeyError as e:
        return Response("'user' and 'pass' params are required", status=400)
    except ValueError:
        return Response("'month' and 'year' must be integers", status=400)
    except Exception as e:
        return Response(f'Error: {e}', status=500)
    try:
        s = backend_obj.login(user, passwd)
        transactions = backend_obj.get_month_transactions(s, month, year, accounts)
        for t in transactions:
            t.category = categorize(auto_category_rules, t)
        serialized_transactions = [ TransactionSerializer(t).data for t in transactions ]
        return Response(serialized_transactions)
    except fetchers.FetchException as e:
        return Response(str(e), status=400)
