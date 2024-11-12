"""
Views for User API
"""

from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token as AuthToken
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings
from rest_framework.response import Response

from user.serializers import UserSerializer, AuthTokenSerializer, ConfirmAccountSerializer

class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Registration successful, we send you a email to confirm your account.'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmAccountView(generics.GenericAPIView):
    """Confirm the user's account using a token."""
    serializer_class = ConfirmAccountSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        auth_token, created = AuthToken.objects.get_or_create(user=user)
        return Response({'message': 'Your account was successful confirmed', 'token': auth_token.key}, status=status.HTTP_200_OK)

class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user