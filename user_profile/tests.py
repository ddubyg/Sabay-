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


class ProfileStatsTests(TestCase):
    """Stats and recent activity come from real data, not hardcoded numbers."""

    def setUp(self):
        from home.models import Activity, Participation
        self.Activity, self.Participation = Activity, Participation
        self.me = User.objects.create_user(username='me', password='password123')
        self.ana = User.objects.create_user(username='ana', password='password123')
        self.ben = User.objects.create_user(username='ben', password='password123')
        self.cy = User.objects.create_user(username='cy', password='password123')
        self.client.login(username='me', password='password123')

    def make(self, title, creator):
        return self.Activity.objects.create(
            title=title, category='study', location='Lib', time='Now',
            description='', creator=creator,
        )

    def test_new_user_has_zero_stats_and_empty_recent(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.context['stats'], {'joined': 0, 'hosted': 0, 'companions': 0})
        self.assertContains(response, 'New to Sabay')
        self.assertContains(response, 'Nothing yet.')
        self.assertNotContains(response, 'Weekend Basketball at Campus Court')

    def test_counts_hosted_joined_and_distinct_companions(self):
        mine = self.make('My Hike', self.me)
        self.Participation.objects.create(activity=mine, user=self.ana)
        self.Participation.objects.create(activity=mine, user=self.ben)

        anas = self.make("Ana's Lunch", self.ana)          # ana again: still one companion
        self.Participation.objects.create(activity=anas, user=self.me)
        self.Participation.objects.create(activity=anas, user=self.ben)

        self.make("Cy's Game", self.cy)                    # not joined: cy is not a companion

        stats = self.client.get(reverse('profile')).context['stats']
        self.assertEqual(stats, {'joined': 1, 'hosted': 1, 'companions': 2})

    def test_recent_lists_hosted_and_joined_newest_first_with_links(self):
        mine = self.make('My Hike', self.me)
        anas = self.make("Ana's Lunch", self.ana)
        self.Participation.objects.create(activity=anas, user=self.me)

        response = self.client.get(reverse('profile'))
        recent = response.context['recent']
        self.assertEqual([(r['kind'], r['activity'].pk) for r in recent],
                         [('joined', anas.pk), ('hosted', mine.pk)])
        self.assertContains(response, reverse('activity_detail', args=[mine.pk]))
        self.assertContains(response, 'Active Member')
        self.assertContains(response, 'just now')

    def test_other_users_activity_does_not_leak_into_my_stats(self):
        theirs = self.make('Not mine', self.ana)
        self.Participation.objects.create(activity=theirs, user=self.ben)
        stats = self.client.get(reverse('profile')).context['stats']
        self.assertEqual(stats, {'joined': 0, 'hosted': 0, 'companions': 0})
