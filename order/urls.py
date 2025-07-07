from django.urls import path
from .views import UserOrderSummaryView, OrderProductStatsView, OrderAnalysisView

urlpatterns = [
    path('api/report/user-order-summary/', UserOrderSummaryView.as_view()),
    path('api/report/order-product-stats/', OrderProductStatsView.as_view()),
    path('api/report/order-analysis/', OrderAnalysisView.as_view()),
]


 

