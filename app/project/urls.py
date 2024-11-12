"""
URL mappings for the recipe app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from project import views


router = DefaultRouter()
router.register('project', views.ProjectViewSet)
router.register('tasks', views.TaskViewSet)
# router.register('ingredients', views.IngredientViewSet)

app_name = 'project'

urlpatterns = [
    path('', include(router.urls)),
]