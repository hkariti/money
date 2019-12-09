from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions import views

router = DefaultRouter()
router.register('accounts', views.AccountViewSet)
router.register('transactions', views.TransactionViewSet, basename='transaction')
router.register('categories', views.CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
