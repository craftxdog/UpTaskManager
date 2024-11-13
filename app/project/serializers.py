"""
Serializer modules API
"""
from django.db.models import Manager
from rest_framework import serializers

from core.models import Project, Task, TaskCompletion


class TaskSerializer(serializers.ModelSerializer):
    """Task serializer"""

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status']
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer class for Project model"""
    tasks = TaskSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = ['id', 'title', 'client_name', 'description', 'manager', 'tasks']
        read_only_fields = ['id', 'manager']

    def get_or_create_tasks(self, tasks, project):
        """Handle getting or creating task as needed."""
        auth_user = self.context['request'].user
        for task_data in tasks:
            task_obj, created = Task.objects.get_or_create(
                completed_by=auth_user,
                **task_data,
            )
            project.tasks.add(task_obj)

    def _get_or_create_team(self, managers, project):
        """Handle getting or creating team as needed."""
        auth_user = self.context['request'].user
        for manager in managers:
            manager_obj, created = Manager.objects.get_or_create(
                user=auth_user,
                **manager,
            )
            project.team.add(manager_obj)

    def create(self, validated_data):
        """Create a project."""
        tasks = validated_data.pop('tasks', [])
        project = Project.objects.create(**validated_data)
        self.get_or_create_tasks(tasks, project)
        return project

    def update(self, instance, validated_data):
        """Update project ."""
        tasks = validated_data.pop('tasks', None)
        if tasks is not None:
            instance.tasks.clear()
            self.get_or_create_tasks(tasks, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProjectDetailSerializer(ProjectSerializer):
    """Serializer for recipe detail view."""

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['description']


class TaskCompletionSerializer(serializers.ModelSerializer):
    """Task completion serializer"""
    task = TaskSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TaskCompletion
        fields = ['id', 'task', 'user', 'status', 'completed_at']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a task completion."""
        return TaskCompletion.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update a task completion."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
