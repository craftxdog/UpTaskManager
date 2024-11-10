"""
Database models
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
import uuid

class UserManager(BaseUserManager):
    """ Manager for users """

    def create_user(self, email, password=None, **extra_fields):
        """ Create, save and return a new user """
        if not email:
            raise ValueError('User must have an email address.')

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """ Create and return a new superuser """

        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):
    """ User in the system """

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'


def get_default_expiration():
    """Get default expiration date"""
    return timezone.now() + timezone.timedelta(minutes=10)

class Token(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(default=get_default_expiration)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return str(self.token)
class Project(models.Model):
    """ Project model """
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    description = models.TextField()
    tasks = models.ManyToManyField(
        'Task',
        related_name='projects',
        blank=True
    )
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='team_projects',
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class TaskStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ON_HOLD = 'onHold', 'On Hold'
    IN_PROGRESS = 'inProgress', 'In Progress'
    UNDER_REVIEW = 'underReview', 'Under Review'
    COMPLETED = 'completed', 'Completed'

class Task(models.Model):
    """ Task model """
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    project = models.ForeignKey(
        'Project',
        related_name='project_tasks',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )
    completed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TaskCompletion',
        related_name='completed_tasks'
    )
    notes = models.ManyToManyField(
        'Note',
        related_name='tasks',
        blank=True
    )

    def __str__(self):
        return self.title
class Note(models.Model):
    """Note model """
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='notes'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Note by {self.created_by} on {self.task}: {self.content}'

    def is_content_valid(self):
        """Validate the content of the note"""
        return len(self.content) > 0

class TaskCompletion(models.Model):
    """ TaskCompletion model """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')