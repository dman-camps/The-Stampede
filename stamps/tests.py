import re
import time
from unittest.mock import patch
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from .models import Stamp, StampParticipation
from .views import email_verified

#uses temporary email storage during tests
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthTests(TestCase):

    #creates sample user and Stamp
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('student', 'student@unomaha.edu', 'Valid-Pass-834!')
        self.stamp = Stamp.objects.create(title='Team event', desc='Public desc', date='2026-11-01', time='12:00', location='Campus', max_participants=10, creator=self.user)

    #registers user and retrieves verification code
    def signup(self, client=None, username='new'):
        client = client or self.client
        response = client.post('/register/', dict(username=username, email=f'{username}@unomaha.edu', password1='Other-Pass-563!', password2='Other-Pass-563!'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', client.session)
        self.assertEqual(mail.outbox[-1].to, [f'{username}@unomaha.edu'])
        return re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()

    #marks user email as verified
    def verify(self):
        EmailAddress.objects.update_or_create(user=self.user, email=self.user.email, defaults={'verified': True, 'primary': True})

    #checks signup verification and code reuse
    def test_signup_verification_and_single_use(self):
        code = self.signup()
        user = User.objects.get(username='new')
        self.assertTrue(user.check_password('Other-Pass-563!'))
        self.assertFalse(email_verified(user))
        self.assertContains(self.client.get('/verify/'), 'code')
        self.client.post('/verify/', {'code': code})
        self.assertTrue(email_verified(user))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertNotIn('account_email_verification_code', self.client.session)
        self.client.logout()
        self.client.post('/verify/', {'code': code})
        self.assertNotIn('_auth_user_id', self.client.session)

    #checks email restrictions and weak passwords
    def test_domain_duplicates_and_weak_password(self):
        self.signup()
        self.client.logout()
        for email in ['NEW@unomaha.edu', 'x@example.com', 'x@unomaha.edu.evil.test']:
            self.client.post('/register/', dict(username='other', email=email, password1='Other-Pass-563!', password2='Other-Pass-563!'))
            self.assertFalse(User.objects.filter(username='other').exists())
        self.client.post('/register/', dict(username='weak', email='weak@unomaha.edu', password1='123', password2='123'))
        self.assertFalse(User.objects.filter(username='weak').exists())

    #checks expired verification codes
    def test_expiration(self):
        code = self.signup()
        session = self.client.session
        session['account_email_verification_code']['at'] = time.time() - 601
        session.save()
        self.client.post('/verify/', {'code': code})
        self.assertFalse(email_verified(User.objects.get(username='new')))
        self.assertNotIn('_auth_user_id', self.client.session)

    #checks verification attempt limits
    def test_attempt_limit(self):
        code = self.signup()
        for _ in range(4):
            self.client.post('/verify/', {'code': '111111' if code != '111111' else '222222'})
        self.client.post('/verify/', {'action': 'resend'})
        self.assertEqual(self.client.session['account_email_verification_code']['failed_attempts'], 4)
        self.client.post('/verify/', {'code': '000000' if code != '000000' else '333333'})
        self.client.post('/verify/', {'code': code})
        self.assertFalse(email_verified(User.objects.get(username='new')))
        self.assertNotIn('account_email_verification_code', self.client.session)

    #checks resend waiting period
    def test_resend_waits_before_sending_again(self):
        self.signup()
        self.client.post('/verify/', {'action': 'resend'})
        self.assertEqual(len(mail.outbox), 1)

    #checks codes cannot verify another account
    def test_account_binding(self):
        code = self.signup()
        other = Client()
        self.signup(other, 'other')
        other.post('/verify/', {'code': code})
        self.assertFalse(email_verified(User.objects.get(username='other')))

    #checks login logout and inactive accounts
    def test_login_logout_and_inactive(self):
        self.client.post('/login/', {'login': 'student', 'password': 'Valid-Pass-834!'})
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.logout()
        self.verify()
        response = self.client.post('/login/', {'login': 'student', 'password': 'Valid-Pass-834!', 'next': 'https://evil.test'})
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.client.get('/logout/')
        self.assertIn('_auth_user_id', self.client.session)
        self.client.post('/logout/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.post('/login/', {'login': 'student', 'password': 'wrong'})
        self.assertNotIn('_auth_user_id', self.client.session)
        self.user.is_active = False
        self.user.save()
        self.client.post('/login/', {'login': 'student', 'password': 'Valid-Pass-834!'})
        self.assertNotIn('_auth_user_id', self.client.session)

    #checks protected pages and changed emails
    def test_protection_and_changed_email(self):
        paths = ['/create/', f'/stamps/{self.stamp.pk}/', f'/stamps/{self.stamp.pk}/join/']
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 302)
        self.client.force_login(self.user)
        for path in paths:
            method = self.client.post if path.endswith('join/') else self.client.get
            self.assertEqual(method(path).status_code, 403)
        self.verify()
        self.assertContains(self.client.get(paths[1]), 'Public desc')
        for email in ['changed@unomaha.edu', 'student@example.com']:
            self.user.email = email
            self.user.save()
            self.assertEqual(self.client.get('/create/').status_code, 403)

    #checks Stamp ownership and unavailable actions
    def test_owner_join_demo_and_no_edit_routes(self):
        self.verify()
        self.client.force_login(self.user)
        response = self.client.post('/create/', dict(title='New', desc='desc', date='2026-11-02', time='13:00', end_time='14:00', location='Criss Library', cost='0', max_participants='5', creator='999'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Stamp.objects.get(title='New').creator, self.user)
        response = self.client.post(f'/stamps/{self.stamp.pk}/join/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(StampParticipation.objects.count(), 1)
        self.assertEqual(self.client.post(f'/stamps/{self.stamp.pk}/').status_code, 405)
        for action in ['edit', 'delete']:
            self.assertEqual(self.client.post(f'/stamps/{self.stamp.pk}/{action}/').status_code, 404)
        self.stamp.refresh_from_db()
        self.assertEqual(self.stamp.title, 'Team event')

    #checks CSRF protection on forms
    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for path in ['/register/', '/login/', '/logout/', '/verify/', '/create/', f'/stamps/{self.stamp.pk}/join/']:
            self.assertEqual(client.post(path).status_code, 403)

    #checks email delivery failures
    def test_failed_delivery_does_not_verify_or_login(self):
        with patch('django.core.mail.message.EmailMultiAlternatives.send', side_effect=OSError('Test mail unavailable')):
            with self.assertRaises(OSError):
                self.signup()
        self.assertFalse(email_verified(User.objects.get(username='new')))
        self.assertNotIn('_auth_user_id', self.client.session)