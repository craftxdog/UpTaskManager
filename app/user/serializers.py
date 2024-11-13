"""
Serializers for Users API Views
"""

from rest_framework import serializers

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound
from core.models import Token
import uuid

from rest_framework.fields import empty

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    password_confirmation = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'password', 'password_confirmation')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
            'password_confirmation': {'write_only': True},
        }

    def validate(self, data):
        """Validate that password and password_confirmation match."""
        password = data.get('password')
        password_confirmation = data.get('password_confirmation')
        if password and password_confirmation and password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")
        if password:
            validate_password(password)
        data.pop('password_confirmation', None)
        return data

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        validated_data.pop('password_confirmation', None)
        user = get_user_model().objects.create_user(**validated_data)
        token = Token.objects.create(
            token=str(uuid.uuid5(uuid.NAMESPACE_DNS, str(user.id))),
            user=user
        )
        try:
            self.send_confirmation_email(user.email, user.name, token.token)
        except Exception as e:
            user.delete()
            raise serializers.ValidationError(f"Error with email confirm: {str(e)}")
        return user

    def send_confirmation_email(self, email, name, token):
        """Send confirmation email to user."""
        subject = 'Confirma tu cuenta'
        from_email = 'no-reply@yourdomain.com'
        confirmation_url = f"http://yourdomain.com/confirm?token={token}"
        html_content = render_to_string('emails/confirm_account_email.html', {
            'name': name,
            'token': token,
            'confirmation_url': confirmation_url,
        })
        message = EmailMultiAlternatives(
            subject=subject,
            body=f"Hola {name}, usa el código {token} para confirmar tu cuenta.",
            from_email=from_email,
            to=[email]
        )
        message.attach_alternative(html_content, "text/html")
        message.send()

    def update(self, instance, validated_data):
        """Update and return an user with encrypted password."""
        password = validated_data.pop('password', None)

        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class ConfirmAccountSerializer(serializers.Serializer):
    """Serializer for the Confirm Account model"""
    token = serializers.CharField()

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.token_instance = None

    def validate(self, attrs):
        """Validate that token is valid."""
        token_value = attrs.get('token')
        try:
            self.token_instance = Token.objects.get(token=token_value)
        except Token.DoesNotExist:
            raise NotFound("Invalid token.")
        return attrs

    def save(self, **kwargs):
        """Confirm user account and delete the token."""
        user = self.token_instance.user
        user.confirmed = True
        user.save()
        self.token_instance.delete()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')
        if not user.confirmed:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
