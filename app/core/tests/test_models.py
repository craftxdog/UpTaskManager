"""
Test for models
"""
import uuid

from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Project, Task, TaskCompletion, Token


def create_user(email='test@exmaple.com', password='test1234'):
    """Create and return test user"""
    return get_user_model().objects.create_user(email, password)


def create_token(user):
    """Create and return a token."""
    return Token.objects.create(user=user, token='12345678')


class ModelTests(TestCase):
    """ Test models """
    def test_create_user_with_email_successful(self):
        """ Test creating a user with an email is successful """
        email = 'test@example.com'
        password = 'test-pass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.confirmed)

    def test_create_token_successful(self):
        """Test creating a token for a user is successful."""
        user = create_user()
        token = Token.objects.create(
            user=user
        )

        self.assertEqual(token.user, user)
        expected_token = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user.id)))
        self.assertEqual(token.token, expected_token)
        self.assertIsNotNone(token.created_at)
        self.assertIsNotNone(token.expires_at)

    def test_token_expiration(self):
        """Test that token expires correctly."""
        user = create_user()
        expected_token = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user.id)))
        token = Token.objects.create(
            token=expected_token,
            user=user
        )

        """Set expiration date manually to simulate expiration"""
        token.created_at = timezone.now() - timedelta(days=1)
        token.save()

        self.assertTrue(token.is_expired())

    def test_new_user_email_normalized(self):
        """ Test email is normalized for new users """
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """ Test that creating a user without an email raises a ValueError """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """ Tests creating a superuser """

        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_project(self):
        """ Tests creating a project """
        email = 'test@example.com'
        password = 'test-pass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        project = Project.objects.create(
            manager=user,
            title='Test Project',
            client_name='Test Client Name',
            description='Test Description',
        )
        self.assertEqual(str(project), project.title)

    def test_create_task(self):
        """ Tests creating a task """
        user = create_user()
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            completed_by=user,
        )
        self.assertEqual(str(task), task.title)

    def test_create_task_completed(self):
        """ Tests creating a completed task """
        user = create_user()
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            completed_by=user,
        )
        completion = TaskCompletion.objects.create(
            task=task,
            user=user,
            status='completed',
        )
        self.assertEqual(completion.status, 'completed')
        self.assertEqual(completion.task, task)
        self.assertEqual(completion.user, user)
