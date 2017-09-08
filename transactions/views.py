import csv
import datetime
from itertools import chain

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.core.serializers import serialize

import transactions.models as models

def index(request):
    return JsonResponse(dict(str="Hello!"))

def get_dummy_account():
    account = models.Accounts.objects.get_or_create(pk=0, defaults=dict(name='dummy'))
    return account[0]

def fill_missing_fields(transaction):
    other_account = get_dummy_account()
    if 'נ"ע' in transaction.description or 'בורסה' in transaction.description:
        other_account = models.Accounts.objects.get_or_create(name="investment")[0]
    if transaction.date.day == 2:
        if transaction.description == 'לאומי ויזה י':
            other_account = models.Accounts.objects.get(name='3349')
        elif transaction.description == 'ל.מסטרקארדי':
            other_account = models.Accounts.objects.get(name='5741')
    if transaction.to_account is None:
        transaction.to_account = other_account
    elif transaction.from_account is None:
        transaction.from_account = other_account

@csrf_exempt
def leumi_credit_dump_multi(request):
    lines_text = (l.decode("utf8") for l in request)
    csv_reader = csv.DictReader(lines_text, dialect='excel')
    csv_reader.fieldnames = ['card', 'deal_date', 'charge_date', 'description', 'deal_type', 'amount', 'currency', 'amount_ils', 'notes']
    new_entries = 0
    total_entries = 0
    dummy_account = get_dummy_account()
    for entry in csv_reader:
        # Skip headers line at the beginning
        if csv_reader.line_num == 1 and entry['card'] == 'card':
            continue
        card = (models.Accounts.objects.get_or_create(name=entry['card']))[0]
        date_parts = [ int(x) for x in entry['deal_date'].split('/') ]
        if date_parts[2] < 100:
            date_parts[2] += 2000
        date_obj = datetime.date(date_parts[2],date_parts[1],date_parts[0])
        (transaction, new_entry) = models.Transactions.objects.get_or_create(date=date_obj, from_account=card, to_account=dummy_account, amount=entry['amount_ils'],original_currency=entry['currency'], amount_original=entry['amount'], notes=entry['notes'], description=entry['description'])
        total_entries += 1
        if new_entry:
            new_entries += 1
    #return render(request, 'credit_dump.j2', dict(csv_text=[next(csv_reader)]), content_type='application/json')
    return JsonResponse(dict(total_entries=total_entries, new_entries=new_entries))

@csrf_exempt
def leumi_bank_dump(request, account):
    lines_text = (l.decode("utf8") for l in request)
    csv_reader = csv.DictReader(lines_text, dialect='excel')
    csv_reader.fieldnames = ['date', 'description', 'confirmation', 'loss', 'gain', 'balance']
    new_entries = 0
    total_entries = 0
    dummy_account = get_dummy_account()
    bank_account = models.Accounts.objects.get(name=account)
    for entry in csv_reader:
        # Skip headers line at the beginning
        if csv_reader.line_num == 1 and entry['date'] in ['date', 'תאריך']:
            continue
        if entry['loss'] and entry['gain']:
            raise Exception("bank movements have to have either loss or gain, not both")
        card = (models.Accounts.objects.get_or_create(name=account))[0]
        date_parts = [ int(x) for x in entry['date'].split('/') ]
        if date_parts[2] < 100:
            date_parts[2] += 2000
        date_obj = datetime.date(date_parts[2],date_parts[1],date_parts[0])
        amount = entry['loss'] or entry['gain']
        transaction = models.Transactions(date=date_obj, amount=amount, description=entry['description'], confirmation=entry['confirmation'])
        if entry['loss']:
            transaction.from_account = bank_account
        else:
            transaction.to_account = bank_account
        fill_missing_fields(transaction)
        try:
            transaction.save()
            new_entries += 1
        except IntegrityError:
            pass
        total_entries += 1
    #return render(request, 'credit_dump.j2', dict(csv_text=[next(csv_reader)]), content_type='application/json')
    return JsonResponse(dict(total_entries=total_entries, new_entries=new_entries))

@csrf_exempt
def rules_dump(request):
    lines_text = (l.decode("utf8") for l in request)
    csv_reader = csv.DictReader(lines_text, dialect='excel')
    csv_reader.fieldnames = ['match', 'category_subcategory', 'type']
    new_entries = 0
    total_entries = 0
    for entry in csv_reader:
        # Skip headers line at the beginning
        if csv_reader.line_num == 1 and entry['match'] == 'match':
            continue
        category_subcategory = entry['category_subcategory'].split('.',1)
        category = models.Categories.objects.get_or_create(title=category_subcategory[0])[0]
        if len(category_subcategory) == 2:
            subcategory = models.Subcategories.objects.get_or_create(title=category_subcategory[1])[0]
        else:
            subcategory = None
        if entry['type'] == 'exact' or not entry['type']:
            entry_type = models.ClusteringRules.TYPE_EXACT
        elif entry['type'] == 'regex':
            entry_type = models.ClusteringRules.TYPE_REGEX
        else:
            raise Exception("Bad match type in entry {0}".forat(total_entries+1))
        (rule, new_entry) = models.ClusteringRules.objects.get_or_create(match=entry['match'],category=category,subcategory=subcategory)
        if new_entry:
            new_entries += 1
        total_entries += 1
    return JsonResponse(dict(total_entries=total_entries, new_entries=new_entries))

@csrf_exempt
def cluster(request):
    transactions = models.Transactions.objects.all()
    total_entries = 0
    changed_entries = 0
    for t in transactions:
        total_entries += 1
        exact_match = models.ClusteringRules.objects.filter(
                type=models.ClusteringRules.TYPE_EXACT,
                match=t.description)
        if len(exact_match) > 0:
            t.category = exact_match[0].category
            t.subcategory = exact_match[0].subcategory
            t.save()
            changed_entries += 1
            continue

    return JsonResponse(dict(total_entries=total_entries, changed_entries=changed_entries))

@csrf_exempt
def get_transactions(request, account=None):
    if account:
        account = models.Accounts.objects.get(name=account)
        transactions_from = account.transactions_from.all()
        transactions_to = account.transactions_to.all()
        transactions = chain(transactions_to, transactions_from)
    else:
        transactions = models.Transactions.objects.all()
    return HttpResponse(serialize('json', transactions))

@csrf_exempt
def get_accounts(request):
    accounts = models.Accounts.objects.all()
    return HttpResponse(serialize('json', accounts))

@csrf_exempt
def get_categories(request):
    categories = models.Categories.objects.all()
    return HttpResponse(serialize('json', categories))

@csrf_exempt
def get_subcategories(request):
    subcategories = models.Subcategories.objects.all()
    return HttpResponse(serialize('json', subcategories))

@csrf_exempt
def get_clustering_rules(request):
    clustering_rules = models.ClusteringRules.objects.all()
    return HttpResponse(serialize('json', clustering_rules))
