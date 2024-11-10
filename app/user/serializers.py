"""
Serializers for Users API Views
"""

from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _



User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    password_confirmation = serializers.CharField(write_only=True, style={'input_type': 'password'})
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'password', 'password_confirmation', 'confirmed')
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
        validated_data['confirmed'] = False
        return User.objects.create_user(**validated_data)
    def update(self, instance, validated_data):
        """Update and return an user with encrypted password."""
        password = validated_data.pop('password', None)

        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
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
            user.confirmed = True
            user.save(update_fields=['confirmed'])

        attrs['user'] = user
        return attrs

# class TokenConfirmSerializer(serializers.Serializer):
#     """Serializer for confirming user account with a token."""
#     token = serializers.UUIDField()
#     def validate_token(self, value):
#         """Validate that the token is valid and has not expired."""
#         try:
#             token_instance = Token.objects.get(token=value)
#         except Token.DoesNotExist:
#             raise serializers.ValidationError(_("Invalid token."))
#         if token_instance.is_expired():
#             raise serializers.ValidationError(_("Token has expired."))
#         return value