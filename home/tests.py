from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Activity, Participation


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


class JoinLeaveTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='password123')
        self.guest = User.objects.create_user(username='guest', password='password123')
        self.activity = Activity.objects.create(
            title='Badminton', category='sports', location='Gym',
            time='Saturday 9 AM', description='Doubles', creator=self.host,
        )
        self.detail_url = reverse('activity_detail', args=[self.activity.pk])
        self.join_url = reverse('join_activity', args=[self.activity.pk])
        self.leave_url = reverse('leave_activity', args=[self.activity.pk])
        self.client.login(username='guest', password='password123')

    def test_host_counts_as_going(self):
        self.assertEqual(self.activity.going_count, 1)

    def test_join_creates_participation(self):
        response = self.client.post(self.join_url, follow=True)
        self.assertRedirects(response, self.detail_url)
        self.assertTrue(Participation.objects.filter(activity=self.activity, user=self.guest).exists())
        self.assertEqual(self.activity.going_count, 2)
        self.assertContains(response, 'Leave Activity')
        self.assertContains(response, 'guest')

    def test_joining_twice_does_not_duplicate(self):
        self.client.post(self.join_url)
        response = self.client.post(self.join_url, follow=True)
        self.assertEqual(Participation.objects.filter(activity=self.activity).count(), 1)
        self.assertContains(response, "already joined")

    def test_leave_removes_participation(self):
        self.client.post(self.join_url)
        response = self.client.post(self.leave_url, follow=True)
        self.assertFalse(Participation.objects.filter(activity=self.activity, user=self.guest).exists())
        self.assertContains(response, 'Join This Activity')

    def test_host_cannot_join_own_activity(self):
        self.client.login(username='host', password='password123')
        response = self.client.post(self.join_url, follow=True)
        self.assertFalse(Participation.objects.exists())
        self.assertContains(response, "You're the host")
        self.assertNotContains(response, 'Join This Activity')

    def test_join_requires_post(self):
        self.assertEqual(self.client.get(self.join_url).status_code, 405)
        self.assertFalse(Participation.objects.exists())

    def test_join_requires_login(self):
        self.client.logout()
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Participation.objects.exists())

    def test_home_feed_shows_real_going_count(self):
        self.client.post(self.join_url)
        response = self.client.get(reverse('home'))
        card = next(a for a in response.context['activities'] if a.pk == self.activity.pk)
        self.assertEqual(card.going_count, 2)
