from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from .models import Stamp, StampParticipation

#tests home feed behavior
class HomeFeedTests(TestCase):

    #creates sample user and Stamp
    def setUp(self):
        self.user = User.objects.create_user('student', 'student@unomaha.edu')
        self.stamp = Stamp.objects.create(title='Campus meetup', desc='Event text',
            date='2026-11-01', time='12:00', location='Library',
            max_participants=10, num_participants=9, creator=self.user)

    #verifies email and signs in user
    def verified_login(self):
        EmailAddress.objects.create(user=self.user, email=self.user.email,
            verified=True, primary=True)
        self.client.force_login(self.user)

    #checks access for anonymous visitors
    def test_anonymous(self):
        response = self.client.get('/')
        self.assertContains(response, 'Welcome to The Stampede')
        self.assertNotContains(response, self.stamp.title)
        self.assertContains(response, reverse('login'))
        self.assertContains(response, reverse('register'))

    #checks access for unverified users
    def test_unverified(self):
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertContains(response, 'Access pending')
        self.assertNotContains(response, self.stamp.title)

    #checks participant counts links and styling
    def test_verified_counts_links_and_css(self):
        self.verified_login()
        StampParticipation.objects.create(user=self.user, stamp=self.stamp)
        response = self.client.get('/')
        self.assertContains(response, '1 / 10 participants')
        self.assertContains(response, reverse('stamp_detail', args=[self.stamp.pk]))
        self.assertContains(response, reverse('create'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertTrue(finders.find('stamps/styles.css'))

    #checks ordering and missing creators
    def test_order_and_null_creator(self):
        self.verified_login()
        early = Stamp.objects.create(title='Early', desc='', date='2026-10-31',
            time='16:00', location='Campus', max_participants=5)
        morning = Stamp.objects.create(title='Morning', desc='', date='2026-11-01',
            time='08:00', location='Campus', max_participants=5)
        tie = Stamp.objects.create(title='Tie', desc='', date=self.stamp.date,
            time=self.stamp.time, location='Campus', max_participants=5)
        response = self.client.get('/')
        self.assertEqual(list(response.context['stamps']), [early, morning, self.stamp, tie])
        self.assertContains(response, 'Unassigned')

    #checks empty feed message
    def test_empty(self):
        self.verified_login()
        Stamp.objects.all().delete()
        self.assertContains(self.client.get('/'), 'No Stamps yet')

    #checks access after email changes
    def test_changed_email(self):
        self.verified_login()
        for email in ['changed@unomaha.edu', 'student@example.com']:
            self.user.email = email
            self.user.save()
            self.assertNotContains(self.client.get('/'), self.stamp.title)

    #checks access for inactive users
    def test_inactive(self):
        self.verified_login()
        self.user.is_active = False
        self.user.save()
        self.assertNotContains(self.client.get('/'), self.stamp.title)

    #checks escaping and read only behavior
    def test_escaping_and_read_only(self):
        self.verified_login()
        self.stamp.title = '<script>alert(1)</script>'
        self.stamp.save()
        response = self.client.get('/')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>')
        self.assertEqual(self.client.post('/').status_code, 405)
        self.assertEqual(Stamp.objects.count(), 1)
        self.assertEqual(StampParticipation.objects.count(), 0)
