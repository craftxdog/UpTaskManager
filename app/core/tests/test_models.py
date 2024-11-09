"""
Test for models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

def create_user(email='test@exmaple.com', password='test1234'):
    """Create and return test user"""
    return get_user_model().objects.create_user(email, password)

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

    # def test_create_project(self):
    #     """ Tests creating a project """
    #     user = get_user_model().objects.create_user(
    #         'test@example.com',
    #         'test123'
    #     )
    #     project = models.Project.objects.create(
    #         project_name='Test Project',
    #         client_name='Test Client Name',
    #         description='Test Description',
    #         user=user,
    #     )
    #     self.assertEqual(str(project), project.project_name)
    #
    # def test_create_task(self):
    #     """ Tests creating a task """
    #     user = create_user()
    #     project = models.Project.objects.create(
    #         project_name='Test Project',
    #         client_name='Test Client',
    #         description='Project Description',
    #         user=user,
    #     )
    #     task = models.Task.objects.create(
    #         name='Test Task',
    #         description='Test Description',
    #         project=project,
    #         status=models.TaskStatus.PENDING,
    #     )
    #
    #     self.assertEqual(str(task), task.name)
    #     self.assertEqual(task.project, project)
    #     self.assertEqual(task.status, models.TaskStatus.PENDING)
    #
    # def test_task_completion(self):
    #     """ Tests creating a task completion entry """
    #     user = create_user()
    #     project = models.Project.objects.create(
    #         project_name='Test Project',
    #         client_name='Test Client',
    #         description='Project Description',
    #         user=user,
    #     )
    #     task = models.Task.objects.create(
    #         name='Test Task',
    #         description='Test Description',
    #         project=project,
    #         status=models.TaskStatus.IN_PROGRESS,
    #     )
    #
    #     # Create TaskCompletion
    #     task_completion = models.TaskCompletion.objects.create(
    #         task=task,
    #         user=user,
    #         status=models.TaskStatus.COMPLETED,
    #     )
    #
    #     self.assertEqual(task_completion.task, task)
    #     self.assertEqual(task_completion.user, user)
    #     self.assertEqual(task_completion.status, models.TaskStatus.COMPLETED)
    #     self.assertIsNotNone(task_completion.completed_at)
    #
    # def test_create_note(self):
    #     """ Tests creating a note """
