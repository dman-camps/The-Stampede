from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Stamp, StampParticipation


class SearchTests(TestCase):
    def setUp(self):
        # Search requires a signed-in student and a verified email.
        self.user = User.objects.create_user('student', 'student@unomaha.edu')
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True, primary=True,
        )
        self.client.force_login(self.user)

        # Free study event with open spaces.
        self.study = Stamp.objects.create(
            title='Biology review', desc='Exam practice', category='study',
            date='2027-01-10', time='12:00', location='Criss Library',
            cost=0, max_participants=2, creator=self.user,
            # Deliberately stale: availability must use actual participation.
            num_participants=99,
        )

        # Paid social event with spaces filled.
        self.social = Stamp.objects.create(
            title='Game night', desc='Meet classmates', category='social',
            date='2027-01-11', time='18:00', location='Student Center',
            cost='5.50', max_participants=2, creator=self.user,
        )
        other = User.objects.create_user('other', 'other@unomaha.edu')
        StampParticipation.objects.create(user=self.user, stamp=self.social)
        StampParticipation.objects.create(user=other, stamp=self.social)

    def check_results(self, filters, expected):
        # Request page and compare it with the expected list.
        response = self.client.get('/', filters)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['stamps']), expected)

    def test_keyword_search(self):
        self.check_results({'q': 'BIOLOGY'}, [self.study])
        self.check_results({'q': 'practice'}, [self.study])

    def test_search_filters(self):
        self.check_results({'category': 'study'}, [self.study])
        self.check_results({'date': '2027-01-10'}, [self.study])
        self.check_results({'location': 'LIBRARY'}, [self.study])
        self.check_results({'max_cost': '0'}, [self.study])
        self.check_results({'max_cost': '5.50'}, [self.study, self.social])
        self.check_results({'available_only': 'on'}, [self.study])

    def test_combined_filters(self):
        self.check_results({'q': 'Biology', 'category': 'study'}, [self.study])
        self.check_results({'q': 'Biology', 'category': 'social'}, [])

    def test_invalid_search(self):
        response = self.client.get('/', {'max_cost': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['search_form'].errors)
        self.assertEqual(list(response.context['stamps']), [])

    def test_search_requires_verified_login(self):
        self.client.logout()
        self.check_results({'q': 'Biology'}, [])
        self.client.force_login(self.user)
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        self.check_results({'q': 'Biology'}, [])

    def test_create_saves_category(self):
        response = self.client.post('/create/', {
            'title': 'New Stamp', 'desc': 'Study together', 'category': 'study',
            'date': '2027-01-12', 'time': '12:00', 'end_time': '13:00',
            'location': 'Criss Library', 'cost': '0', 'max_participants': '5',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Stamp.objects.get(title='New Stamp').category, 'study')
