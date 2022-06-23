from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.client = {
            'guest': Client(),
            'auth': Client(),
        }
        self.client['auth'].force_login(UsersURLTests.user)

        self.app_url = '/auth/'
        self.urls_to_check = {
            'signup/':
                ('users/signup.html',
                 'guest'),
            'login/':
                ('users/login.html',
                 'guest'),
            'password_change/':
                ('users/password_change_form.html',
                 'auth'),
            'password_change/done/':
                ('users/password_change_done.html',
                 'auth'),
            'password_reset/':
                ('users/password_reset_form.html',
                 'guest'),
            'password_reset/done/':
                ('users/password_reset_done.html',
                 'guest'),
            'reset/<uidb64>/<token>/':
                ('users/password_reset_confirm.html',
                 'guest'),
            'reset/done/':
                ('users/password_reset_complete.html',
                 'guest'),
            'logout/':
                ('users/logged_out.html',
                 'guest'),
        }

    def test_about_url_exists_at_desired_location(self):
        """Проверяем доступность всех адресов."""
        for url, (template, access) in self.urls_to_check.items():
            expected_status = {
                'guest': HTTPStatus.OK,
                'auth': HTTPStatus.OK,
            }
            if access == 'auth':
                expected_status['guest'] = HTTPStatus.FOUND
            for user in expected_status:
                with self.subTest(url=url, access=access, user=user):
                    responce = self.client[user].get(self.app_url + url)
                    self.assertEqual(responce.status_code,
                                     expected_status[user])

    def test_about_url_uses_correct_template(self):
        """Проверяем корректность шаблонов."""
        for url, (template, access) in self.urls_to_check.items():
            with self.subTest(url=url, template=template):
                response = self.client['auth'].get(self.app_url + url)
                self.assertTemplateUsed(response, template)
