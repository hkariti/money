from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions import views

router = DefaultRouter()
router.register('auth_sources', views.AuthSourceViewSet)
router.register('accounts', views.AccountViewSet)
router.register('transactions', views.TransactionViewSet)
router.register('categories', views.CategoryViewSet)
router.register('pattern', views.PatternViewSet)

urlpatterns = [
    path('fetch/<slug:backend>', views.fetch_view),
    path('', include(router.urls)),
]
