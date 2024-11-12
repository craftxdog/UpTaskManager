"""
Tests for tasks api
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Task, Project

from project.serializers import TaskSerializer
from yaml import serialize

TASKS_URL = reverse('project:task-list')
def detail_url(task_id):
    """Return task's detail url'"""
    return reverse('project:task-detail', args=[task_id])

def create_user(email='user@example.com', password='pass1234'):
    """Create a user"""
    return get_user_model().objects.create_user(email, password)

class PublicTasksApiTests(TestCase):
    """Tests for public tasks api"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tasks"""
        res = self.client.get(TASKS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    class PrivateTasksApiTests(TestCase):
        """Tests for private tasks api"""
        def setUp(self):
            self.user = create_user()
            self.client = APIClient()
            self.client.force_authenticate(self.user)

        def test_retrieve_tasks(self):
            """Test retrieving tasks"""
            Task.objects.create(completed_by=self.user, title='title', description='description')
            Task.objects.create(completed_by=self.user, title='title-2', description='description')
            res = self.client.get(TASKS_URL)

            tasks = Task.objects.all().order_by('-title')
            serializer = TaskSerializer(tasks, many=True)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data, serializer.data)

        def test_tasks_limited_to_user(self):
            """Test list of tasks is limited to authenticated user."""
            user2 = create_user(email='user2@example.com')
            Task.objects.create(completed_by=self.user, title='Fruity')
            task = Task.objects.create(completed_by=self.user, title='Comfort Food')

            res = self.client.get(TASKS_URL)

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(len(res.data), 1)
            self.assertEqual(res.data[0]['title'], task.title)
            self.assertEqual(res.data[0]['id'], task.id)

        def test_update_task(self):
            """Test updating a task."""
            task = Task.objects.create(completed_by=self.user, title='After Dinner')

            payload = {'title': 'Dessert'}
            url = detail_url(task.id)
            res = self.client.patch(url, payload)

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            task.refresh_from_db()
            self.assertEqual(task.title, payload['title'])

        def test_delete_task(self):
            """Test deleting a task"""
            task = Task.objects.create(completed_by=self.user, title='Breakfast')

            url = detail_url(task.id)
            res = self.client.delete(url)

            self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
            tasks = Task.objects.filter(completed_by=self.user)
            self.assertFalse(tasks.exists())

        def test_filter_tasks_assigned_to_project(self):
            """Test listing tasks to those assigned to recipes."""
            task1 = Task.objects.create(completed_by=self.user, title='Breakfast')
            task2 = Task.objects.create(completed_by=self.user, title='Lunch')
            project = Project.objects.create(
                title='Green Eggs on Toast',
                description='This is a green egg on toast',
                client_name='Client Name',
                manager=self.user,
            )
            project.tasks.add(task1)

            res = self.client.get(TASKS_URL, {'assigned_only': 1})

            s1 = TaskSerializer(task1)
            s2 = TaskSerializer(task2)
            self.assertIn(s1.data, res.data)
            self.assertNotIn(s2.data, res.data)

        def test_filtered_tasks_unique(self):
            """Test filtered tasks returns a unique list."""
            task = Task.objects.create(completed_by=self.user, title='Breakfast', description='This is a green egg on toast')
            Task.objects.create(completed_by=self.user, title='Dinner', description='This is a green egg on toast buuuf')
            project1 = Project.objects.create(
                title='Pancakes',
                description='This is a pancakes',
                client_name='Client Name',
                manager=self.user,
            )
            project2 = Project.objects.create(
                title='Porridge',
                description='This is a porridge',
                client_name='Client Name',
                manager=self.user,
            )
            project1.tasks.add(task)
            project2.tasks.add(task)

            res = self.client.get(TASKS_URL, {'assigned_only': 1})

            self.assertEqual(len(res.data), 1)