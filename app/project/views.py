"""
Views for the recipe APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import models
from core.models import (
    Project,
    Task,
)
from project.serializers import ProjectSerializer, ProjectDetailSerializer, TaskSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tasks',
                OpenApiTypes.STR,
                description='Comma separated list of tasks IDs to filter',
            ),
            OpenApiParameter(
                'team',
                OpenApiTypes.STR,
                description='Comma separated list of team IDs to filter',
            ),
        ]
    )
)
class ProjectViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = ProjectDetailSerializer
    queryset = Project.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        tasks = self.request.query_params.get('tasks')
        team = self.request.query_params.get('team')
        queryset = self.queryset
        if tasks:
            task_ids = self._params_to_ints(tasks)
            queryset = queryset.filter(tasks__id__in=task_ids)
        if team:
            team_ids = self._params_to_ints(team)
            queryset = queryset.filter(team__id__in=team_ids)

        return queryset.filter(
            manager=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return ProjectSerializer
        elif self.action == 'upload_image':
            return ProjectSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new project."""
        serializer.save(manager=self.request.user)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.',
            ),
        ]
    )
)
class BaseProjectAttrViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base view_set for project attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filtra el queryset al usuario autenticado o sus tareas."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(project__isnull=False)

        return queryset.filter(
            models.Q(project__manager=self.request.user) | models.Q(completed_by=self.request.user)
        ).order_by('-title').distinct()


class TaskViewSet(BaseProjectAttrViewSet):
    """Manage task in the database."""
    serializer_class = TaskSerializer
    queryset = Task.objects.all()
