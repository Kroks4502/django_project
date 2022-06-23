from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.client = {
            'guest': Client(),
            'auth': Client(),
        }
        self.client['auth'].force_login(UsersViewTest.user)

        self.urls_to_check = {
            reverse('users:signup'):
                ('users/signup.html',
                 'guest'),
            reverse('users:login'):
                ('users/login.html',
                 'guest'),
            reverse('users:password_change_form'):
                ('users/password_change_form.html',
                 'auth'),
            reverse('users:password_change_done'):
                ('users/password_change_done.html',
                 'auth'),
            reverse('users:password_reset_form'):
                ('users/password_reset_form.html',
                 'guest'),
            reverse('users:password_reset_done'):
                ('users/password_reset_done.html',
                 'guest'),
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': '12345', 'token': '12345'}):
                ('users/password_reset_confirm.html',
                 'guest'),
            reverse('users:password_reset_complete'):
                ('users/password_reset_complete.html',
                 'guest'),
            reverse('users:logout'):
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
                with self.subTest(url=url, access=access):
                    responce = self.client[user].get(url)
                    self.assertEqual(responce.status_code,
                                     expected_status[user])

    def test_about_url_uses_correct_template(self):
        """Проверяем корректность шаблонов."""
        for url, (template, access) in self.urls_to_check.items():
            with self.subTest(url=url, template=template):
                response = self.client['auth'].get(url)
                self.assertTemplateUsed(response, template)

    def test_users_singup_page_show_correct_context(self):
        """Шаблон signup сгенерирован с правильным контекстом."""
        response = self.client['guest'].get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value, expected=expected):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)
