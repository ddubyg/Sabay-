from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Activity


class HomeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='hometestuser',
            password='password123'
        )
        self.client.login(username='hometestuser', password='password123')

    def test_home_page_renders_with_activities_and_context(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back, hometestuser.')
        self.assertContains(response, 'Explore by category')
        self.assertContains(response, 'Upcoming activities')
        self.assertContains(response, 'Post Sabay')
        self.assertContains(response, reverse('create_activity'))
        self.assertIn('user_settings', response.context)

    def test_create_activity_page_renders(self):
        response = self.client.get(reverse('create_activity'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Post a New Sabay Activity')

    def test_create_activity_post_success(self):
        response = self.client.post(reverse('create_activity'), {
            'title': 'Midterm Study Group',
            'category': 'study',
            'location': 'Library 2F',
            'time': 'Friday at 2 PM',
            'description': 'Let us study Calculus and Physics together.',
        }, follow=True)

        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'New Sabay activity posted successfully!')
        self.assertTrue(Activity.objects.filter(title='Midterm Study Group').exists())
