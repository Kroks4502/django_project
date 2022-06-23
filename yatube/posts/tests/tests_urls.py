from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User
from . import TEST_USERNAME_AUTH


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Обычный пользователь
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)

        # Автор публикации
        cls.author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.author,
        )

    def setUp(self):
        self.client = {
            'guest': Client(),
            'author': Client(),
            'auth': Client(),
        }
        self.client['author'].force_login(PostURLTests.author)
        self.client['auth'].force_login(PostURLTests.user)
        self.urls_to_check = {
            '/':
                ('posts/index.html',
                 'guest'),
            '/follow/':
                ('posts/follow.html',
                 'auth'),
            f'/group/{PostURLTests.group.slug}/':
                ('posts/group_list.html',
                 'guest'),
            f'/profile/{PostURLTests.user.username}/':
                ('posts/profile.html',
                 'guest'),
            f'/posts/{PostURLTests.post.pk}/':
                ('posts/post_detail.html',
                 'guest'),
            f'/posts/{PostURLTests.post.pk}/edit/':
                ('posts/create_post.html',
                 'author'),
            '/create/':
                ('posts/create_post.html',
                 'auth'),
            '/unexisting_page/':
                ('core/404.html',
                 ''),
        }

    def test_about_url_exists_at_desired_location(self):
        """Проверить доступность адресов."""
        for url, (template, access) in self.urls_to_check.items():
            expected_status = {
                'guest': HTTPStatus.OK,
                'auth': HTTPStatus.OK,
            }
            if access == 'auth':
                expected_status['guest'] = HTTPStatus.FOUND
            elif access == 'author':
                expected_status['guest'] = HTTPStatus.FOUND
                expected_status['auth'] = HTTPStatus.FOUND
                expected_status['author'] = HTTPStatus.OK
            elif access == '':
                expected_status = {
                    'guest': HTTPStatus.NOT_FOUND,
                }
            for user in expected_status:
                with self.subTest(url=url, access=access, user=user):
                    response = self.client[user].get(url)
                    self.assertEqual(response.status_code,
                                     expected_status[user])

    def test_about_url_uses_correct_template(self):
        """Проверяем корректность шаблонов."""
        for url, (template, *other) in self.urls_to_check.items():
            if template:
                with self.subTest(url=url, template=template):
                    response = self.client['author'].get(url)
                    self.assertTemplateUsed(response, template)
