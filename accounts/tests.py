from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from user_profile.models import Profile
from settings_app.models import UserSettings


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_page_renders_and_contains_create_account_link(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back')
        self.assertContains(response, 'Create account')
        self.assertContains(response, reverse('register'))

    def test_register_page_renders_properly(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an account')
        self.assertContains(response, 'Username')
        self.assertContains(response, 'Email Address')
        self.assertContains(response, 'Password')
        self.assertContains(response, 'Confirm Password')
        self.assertContains(response, 'Create account')
        self.assertContains(response, reverse('login'))

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match.')

    def test_register_duplicate_username(self):
        User.objects.create_user(username='existinguser', password='password123')
        response = self.client.post(reverse('register'), {
            'username': 'existinguser',
            'email': 'unique@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already exists.')

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'testregistration',
            'email': 'testregistration@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
        }, follow=True)

        self.assertRedirects(response, reverse('login'))
        self.assertContains(response, 'Account created successfully! Please log in.')

        # Verify user exists in DB
        user = User.objects.filter(username='testregistration').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'testregistration@example.com')

        # Verify Profile and UserSettings were created
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(UserSettings.objects.filter(user=user).exists())

        # Verify user can log in with these credentials
        login_response = self.client.post(reverse('login'), {
            'username': 'testregistration',
            'password': 'securepassword123',
        }, follow=True)
        self.assertRedirects(login_response, reverse('home'))
        self.assertContains(login_response, 'Welcome back, testregistration.')
