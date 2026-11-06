from django.urls import path

from .views import SessionDetailView, SessionListCreateView

urlpatterns = [
    path('', SessionListCreateView.as_view(), name='session_list_create'),
    path('<int:pk>/', SessionDetailView.as_view(), name='session_detail'),
]
