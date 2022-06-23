from django.db import IntegrityError
from django.test import TestCase

from . import TEST_USERNAME_AUTH
from ..models import Group, Post, User, Follow, Comment


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Т' * 16,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Т' * 16,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

        comment = PostModelTest.comment
        expected_object_name = comment.text[:15]
        self.assertEqual(expected_object_name, str(comment))

    def test_models_have_correct_verbose_name(self):
        """Проверяем, что verbose_name в полях совпадает с ожидаемым."""
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Изображение',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_value)

    def test_models_have_correct_help_text(self):
        """Проверяем, что help_text в полях совпадает с ожидаемым"""
        field_verbose = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
            'image': 'Выберите изображение',
        }
        for field, expected_value in field_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).help_text,
                    expected_value)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)

    def test_user_no_self_follow(self):
        """Проверяем, что модель не позволяет пользователю
        подписаться на самого себя."""
        with self.assertRaisesMessage(IntegrityError, 'prevent_self_follow'):
            Follow.objects.create(
                user=FollowModelTest.user, author=FollowModelTest.user)

    def test_user_no_double_follow_on_author(self):
        """Проверяем, что модель не позволяет пользователю
        повторно подписаться на одного автора."""
        author = User.objects.create_user(username='author')
        Follow.objects.create(user=FollowModelTest.user, author=author)
        constraint_name = 'UNIQUE constraint failed'
        with self.assertRaisesMessage(IntegrityError, constraint_name):
            Follow.objects.create(user=FollowModelTest.user, author=author)
