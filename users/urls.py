from django.urls import path
from .views import RegisterView
from .views import LoginView
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
]
