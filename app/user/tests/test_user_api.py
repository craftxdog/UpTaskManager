"""
Test User API endpoints
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create-account')
CREATE_TOKEN_URL = reverse('user:create-token')
PROFILE_URL = reverse('user:profile')

def create_user(**params):
    """Create a user with the given parameters."""
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the users API (public)"""
    def setUp(self):
        self.client = APIClient()
    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful."""
        payload = {
            'email': 'user@example.com',
            'password': '@user1234',
            'password_confirmation': '@user1234',
            'name': 'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating a user that already exists fails."""
        payload = {
            'email': 'test2@example.com',
            'password': '@user1234',
            'name': 'Test name',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, {**payload, 'password_confirmation': '@user1234'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch_error(self):
        """Test that creating a user fails if passwords do not match."""
        payload = {
            'email': 'user@example.com',
            'name': 'Test User',
            'password': '@user1234',
            'password_confirmation': 'wrong_password',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', res.data)

    def test_password_too_short(self):
        """Test that password must be more than 8 characters."""
        payload = {
            'email': 'user@example.com',
            'password': 'pw',
            'name': 'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            'name': 'Test Name',
            'email': 'testers@example.com',
            'password': 'test-user-password123',
            'password_confirmation': 'test-user-password123'
        }
        user_details.pop('password_confirmation')
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(email='test@example.com', password='goodpass')

        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email."""
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='test-123',
            name='Test Name',
            confirmed=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'id': int(self.user.id),
            'name': self.user.name,
            'email': self.user.email,
            'confirmed': self.user.confirmed,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(PROFILE_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {'name': 'Updated name', 'password': 'new-password123'}

        res = self.client.patch(PROFILE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)



    # def test_retrieve_user_unauthorized(self):
    #     """Test authentication is required for users."""
    #     res = self.client.get(ME_URL)
    #
    #     self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_confirm_account_with_valid_token(self):
    #     """Test confirming a user's account with a valid token."""
    #     user = create_user(
    #         email='confirm@example.com',
    #         password='@user1234',
    #         name='Test User'
    #     )
    #     token = Token.objects.create(user=user)
    #
    #     payload = {
    #         'token': str(token.token)
    #     }
    #
    #     res = self.client.post(CONFIRM_USER_URL, payload)
    #
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     user.refresh_from_db()
    #     self.assertTrue(user.confirmed)
    #
    # def test_confirm_account_with_invalid_token(self):
    #     """Test that confirming a user's account with an invalid token fails."""
    #     payload = {
    #         'token': 'invalid-token'
    #     }
    #
    #     res = self.client.post(CONFIRM_USER_URL, payload)
    #
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    #
    # def test_confirm_account_with_expired_token(self):
    #     """Test that confirming a user's account with an expired token fails."""
    #     user = create_user(
    #         email='expired@example.com',
    #         password='@user1234',
    #         name='Test User'
    #     )
    #     token = Token.objects.create(user=user)
    #     token.expires_at = '2024-01-01T00:00:00Z'
    #     token.save()
    #
    #     payload = {
    #         'token': str(token.token)
    #     }
    #
    #     res = self.client.post(CONFIRM_USER_URL, payload)
    #
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)