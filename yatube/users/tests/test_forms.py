from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersFormTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_singup_create_new_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Тест',
            'last_name': 'Тестовой',
            'username': 'test',
            'email': 'test@test.test',
            'password1': 'DkMu3A7Vk@AWy3p',
            'password2': 'DkMu3A7Vk@AWy3p',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(User.objects.filter(
            first_name='Тест',
            last_name='Тестовой',
            username='test',
            email='test@test.test').exists())
