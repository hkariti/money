from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions import views

router = DefaultRouter()
router.register('accounts', views.AccountViewSet)
router.register('transactions', views.TransactionViewSet)
router.register('categories', views.CategoryViewSet)

urlpatterns = [
    path('fetch/leumicard', views.fetch_leumicard_view),
    path('fetch/leumi', views.fetch_leumi_view),
    path('', include(router.urls)),
]
