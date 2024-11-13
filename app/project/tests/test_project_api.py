"""

"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Project, Task

from project.serializers import ProjectSerializer, ProjectDetailSerializer


PROJECT_URL = reverse('project:project-list')


def detail_url(project_id):
    """Create and return a project detail URL."""
    return reverse('project:project-detail', args=[project_id])


def create_project(manager, **params):
    """Create and return a sample user."""
    defaults = {
        'title': 'Sample project title',
        'description': 'Sample project description',
        'client_name': 'Client name',
    }
    defaults.update(params)
    project = Project.objects.create(manager=manager, **defaults)
    return project


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(PROJECT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_project(self):
        """Test retrieving a list of project."""
        create_project(manager=self.user)
        create_project(manager=self.user)

        res = self.client.get(PROJECT_URL)

        project = Project.objects.all().order_by('-id')
        serializer = ProjectSerializer(project, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_project_list_limited_to_user(self):
        """Test list of project is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='test123')
        create_project(manager=other_user)
        create_project(manager=self.user)

        res = self.client.get(PROJECT_URL)

        project = Project.objects.filter(manager=self.user)
        serializer = ProjectSerializer(project, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_project_detail(self):
        """Test get project detail."""
        project = create_project(manager=self.user)

        url = detail_url(project.id)
        res = self.client.get(url)

        serializer = ProjectDetailSerializer(project)
        self.assertEqual(res.data, serializer.data)

    def test_create_project(self):
        """Test creating a project."""
        payload = {
            'title': 'Sample project',
            'description': 'Sample project',
            'client_name': 'Client name',
            'manager': self.user.id
        }
        res = self.client.post(PROJECT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=res.data['id'])

        for k, v in payload.items():
            if k == "manager":
                self.assertEqual(project.manager.id, v)
            else:
                self.assertEqual(getattr(project, k), v)
        self.assertEqual(project.manager, self.user)

    def test_partial_update(self):
        """Test partial update of a project."""
        project = create_project(
            manager=self.user,
            title='Sample project',
            client_name='Client name',
            description='Sample project',
        )
        payload = {'title': 'New project title'}
        url = detail_url(project.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.title, payload['title'])
        self.assertEqual(project.manager, self.user)

    def test_full_update(self):
        """Test full update of project."""
        project = create_project(
            manager=self.user,
            title='Sample project',
            client_name='Client name',
            description='Sample project',
        )
        payload = {
            'title': 'New project title',
            'description': 'New project description',
            'client_name': 'Client name',
        }
        url = detail_url(project.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        for k, v in payload.items():
            if k == "manager":
                self.assertEqual(project.manager.id, v)
            else:
                self.assertEqual(getattr(project, k), v)
        self.assertEqual(project.manager, self.user)

    def test_update_user_returns_error(self):
        """Test changing the project user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        project = create_project(manager=self.user)

        payload = {'manager': new_user.id}
        url = detail_url(project.id)
        self.client.patch(url, payload)

        project.refresh_from_db()
        self.assertEqual(project.manager, self.user)

    def test_delete_project(self):
        """Test deleting a project successful."""
        project = create_project(manager=self.user)

        url = detail_url(project.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_project_other_users_project_error(self):
        """Test trying to delete another users project gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        project = create_project(manager=new_user)

        url = detail_url(project.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_create_project_with_new_tasks(self):
        """Test creating a recipe with new tasks."""
        payload = {
            'title': 'Thai Prawn Curry',
            'description': 'Thai Prawn Curry',
            'client_name': 'Client name',
            'tasks': [
                {'title': 'Prepare Ingredients', 'description': 'Gather all ingredients for the curry.'},
                {'title': 'Cook Curry', 'description': 'Follow steps to cook the curry.'},
            ],
        }
        res = self.client.post(PROJECT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        projects = Project.objects.filter(manager=self.user)
        self.assertEqual(projects.count(), 1)
        project = projects[0]
        self.assertEqual(project.tasks.count(), 2)
        for task in payload['tasks']:
            exists = project.tasks.filter(
                title=task['title'],
                description=task['description'],
                completed_by=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_project_with_existing_tasks(self):
        """Test creating a project with existing task."""
        task_indian = Task.objects.create(title='Indian', description='Indians food', status='Pending', completed_by=self.user)
        payload = {
            'title': 'Thai',
            'description': 'Thai Curry',
            'client_name': 'Client name',
            'tasks': [
                {'title': 'Indian', 'description': 'Indians food'},
                {'title': 'task title 3', 'description': 'task description 3'},
            ],
        }
        res = self.client.post(PROJECT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        projects = Project.objects.filter(manager=self.user)
        self.assertEqual(projects.count(), 1)
        project = projects[0]
        self.assertEqual(project.tasks.count(), 2)
        self.assertIn(task_indian, project.tasks.all())
        for task in payload['tasks']:
            exists = project.tasks.filter(
                title=task['title'],
                completed_by=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_task_on_update(self):
        """Test create task when updating a project."""
        project = create_project(manager=self.user)

        payload = {'tasks': [{'title': 'Lunch', 'description': 'Lunch'}]}
        url = detail_url(project.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_task = Task.objects.get(title='Lunch')
        self.assertIn(new_task, project.tasks.all())

    def test_update_project_assign_task(self):
        """Test assigning an existing project when updating a project."""
        task_breakfast = Task.objects.create(title='Breakfast', description='Breakfast', completed_by=self.user)
        project = create_project(title='Breakfast', client_name='Breakfast', description='Breakfast', manager=self.user)
        project.tasks.add(task_breakfast)
        task_lunch = Task.objects.create(title='Lunch', description='Lunch', completed_by=self.user)
        payload = {'tasks': [{'title': 'Lunch', 'description': 'Lunch'}]}

        url = detail_url(project.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(task_lunch, project.tasks.all())
        self.assertNotIn(task_breakfast, project.tasks.all())
