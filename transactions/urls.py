from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^dump/leumi/credit/multi$', views.leumi_credit_dump_multi, name='dump_leumi_credit_multi'),
    url(r'^dump/leumi/bank/(?P<account>\w+)$', views.leumi_bank_dump, name='dump_leumi_bank'),
    url(r'^dump/clustering_rules', views.rules_dump, name='dump_clustering_rules'),
    url(r'^cluster', views.cluster, name='cluster'),
    url(r'^get/transactions/(?P<account>\w+)', views.get_transactions, name='get_transactions'),
    url(r'^get/transactions', views.get_transactions, name='get_all_transactions'),
    url(r'^get/accounts', views.get_accounts, name='get_all_accounts'),
    url(r'^get/categories', views.get_categories, name='get_all_categories'),
    url(r'^get/subcategories', views.get_subcategories, name='get_all_subcategories'),
    url(r'^get/clustering_rules', views.get_clustering_rules, name='get_all_clustering_rules'),
]
