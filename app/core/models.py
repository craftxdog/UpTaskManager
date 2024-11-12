"""
Database models
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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

    objects = UserManager()

    USERNAME_FIELD = 'email'


class Token(models.Model):
    """Token for confirm account"""
    token = models.CharField(max_length=255, unique=True, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(self.user.id)))
        if not self.created_at:
            self.created_at = timezone.now()
        if not self.expires_at or self.created_at != self.__original_created_at:
            self.expires_at = self.created_at + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at
    class Meta:
        indexes = [
            models.Index(fields=['expires_at']),
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_created_at = self.created_at


class Project(models.Model):
    """ Project model """
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    description = models.TextField()
    tasks = models.ManyToManyField('Task')
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='team_projects',
        blank=True
    )
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
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )
    completed_by =models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    # notes_list = models.ManyToManyField('Note', related_name='tasks', blank=True)
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
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='note_task')
    def __str__(self):
        return f'Note by {self.created_by} on {self.task}: {self.content}'


class TaskCompletion(models.Model):
    """ TaskCompletion model """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )

    class Meta:
        unique_together = ('task', 'user')