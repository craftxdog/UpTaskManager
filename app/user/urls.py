"""
Url Mappings for user API
"""

from django.urls import path
from user import views


app_name = 'user'

urlpatterns = [
    path('create-account/', views.CreateUserView.as_view(), name='create-account'),
    path('create-token/', views.CreateTokenView.as_view(), name='create-token'),
    path('profile/', views.ManageUserView.as_view(), name='profile'),
]