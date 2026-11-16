from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile


class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profiletestuser',
            password='password123',
            email='profile@test.com'
        )
        self.client.login(username='profiletestuser', password='password123')

    def test_profile_page_renders(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profiletestuser')
        self.assertContains(response, 'About You')
        self.assertContains(response, 'Interests & Vibes')
        self.assertContains(response, reverse('edit_profile'))

    def test_edit_profile_page_renders(self):
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Profile')
        self.assertContains(response, 'Course / Major')

    def test_edit_profile_post(self):
        response = self.client.post(reverse('edit_profile'), {
            'course': 'BS Information Technology',
            'year_level': '3rd Year',
            'bio': 'Passionate about web dev and basketball.',
            'email': 'updated_profile@test.com'
        }, follow=True)

        self.assertRedirects(response, reverse('profile'))
        self.assertContains(response, 'Profile updated successfully!')

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.course, 'BS Information Technology')
        self.assertEqual(profile.year_level, '3rd Year')
        self.assertEqual(profile.bio, 'Passionate about web dev and basketball.')

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated_profile@test.com')
