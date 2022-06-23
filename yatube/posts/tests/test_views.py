import datetime
import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ..models import Follow, Group, Post, User
from ..settings import DEFAULT_AMOUNT_POSTS_ON_PAGE
from . import (REVERSE_CASH, TEST_GROUP_SLUG,
               TEST_USERNAME_AUTH, UPLOADED_IMAGE, DISABLE_CACHING)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(**DISABLE_CACHING)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.user,
        )
        cls.rev_cash = {
            'posts:post_detail.test_kwargs':
                reverse('posts:post_detail',
                        kwargs={'post_id': cls.post.pk}),
            'posts:post_edit.test_kwargs':
                reverse('posts:post_edit',
                        kwargs={'post_id': cls.post.pk}),
        }
        cls.rev_cash.update(REVERSE_CASH)
        cls.templates_page_names = {
            cls.rev_cash.get('posts:index'):
                'posts/index.html',
            cls.rev_cash.get('posts:follow_index'):
                'posts/follow.html',
            cls.rev_cash.get('posts:group_detail'):
                'posts/group_detail.html',
            cls.rev_cash.get('posts:group_list.test_kwargs'):
                'posts/group_list.html',
            cls.rev_cash.get('posts:profile.test_kwargs'):
                'posts/profile.html',
            cls.rev_cash.get('posts:post_detail.test_kwargs'):
                'posts/post_detail.html',
            cls.rev_cash.get('posts:post_edit.test_kwargs'):
                'posts/create_post.html',
            cls.rev_cash.get('posts:post_create'):
                'posts/create_post.html',
        }

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostPagesTests.user)

    def test_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имен страниц, доступен."""
        for url in PostPagesTests.templates_page_names:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template(self):
        """Проверяем корректность шаблонов."""
        for url, template in PostPagesTests.templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:index'))
        self.assertEqual(response.context.get('page_name'),
                         'Последние обновления на сайте')
        self.assertEqual(response.context.get('page_obj').object_list,
                         [PostPagesTests.post])

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:group_list.test_kwargs'))
        self.assertEqual(response.context.get('group'),
                         PostPagesTests.group)
        self.assertEqual(response.context.get('page_obj').object_list,
                         [PostPagesTests.post])

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:profile.test_kwargs'))
        self.assertEqual(response.context.get('author'),
                         PostPagesTests.user)
        self.assertEqual(response.context.get('page_obj').object_list,
                         [PostPagesTests.post])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:post_detail.test_kwargs'))
        self.assertEqual(response.context.get('post'), PostPagesTests.post)
        self.assertIsInstance(response.context['form'].fields['text'],
                              forms.fields.CharField)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:post_edit.test_kwargs'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value, expected=expected):
                self.assertIsInstance(
                    response.context['form'].fields[value], expected)
        actual_form = response.context.get('form').initial
        expected = PostPagesTests.post
        self.assertTrue(response.context.get('is_edit'))
        self.assertEqual(actual_form.get('text'), expected.text)
        self.assertEqual(actual_form.get('group'), expected.group.pk)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_client.get(
            PostPagesTests.rev_cash.get('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value, expected=expected):
                form_field = response.context.get('form').fields[value]
                self.assertIsInstance(form_field, expected)


@override_settings(**DISABLE_CACHING)
class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create([
            Post(pk=num,
                 text=f'Тестовый пост {num}',
                 group=cls.group,
                 author=cls.user,
                 ) for num in range(13)
        ])
        for post in cls.posts:
            post.pub_date = timezone.now() + datetime.timedelta(days=post.pk)
        Post.objects.bulk_update(cls.posts, ['pub_date'])

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PaginatorTests.user)
        self.pages = [
            REVERSE_CASH.get('posts:index'),
            REVERSE_CASH.get('posts:group_list.test_kwargs'),
            REVERSE_CASH.get('posts:profile.test_kwargs'),
        ]

    def test_first_page_contains_ten_records(self):
        """Проверяем, что на первой странице каждого раздела 10 постов."""
        for page in self.pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    DEFAULT_AMOUNT_POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверяем, что на второй странице каждого раздела 3 поста."""
        expected_amount = (len(PaginatorTests.posts)
                           - DEFAULT_AMOUNT_POSTS_ON_PAGE)
        for page in self.pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page + '?page=2')
                self.assertEqual(
                    len(response.context.get('page_obj').object_list),
                    expected_amount)

    def test_first_page_contents_on_page(self):
        """Проверяем, что на первой странице публикации отсортированы
        в порядке убывания даты публикации."""
        expected_len = (len(PaginatorTests.posts)
                        - DEFAULT_AMOUNT_POSTS_ON_PAGE - 1)
        for page in self.pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertEqual(
                    response.context.get('page_obj').object_list,
                    PaginatorTests.posts[:expected_len:-1])

    def test_second_page_contents_on_page(self):
        """Проверяем, что на первой странице публикации отсортированы
        в порядке убывания даты публикации."""
        expected_len = (len(PaginatorTests.posts)
                        - DEFAULT_AMOUNT_POSTS_ON_PAGE - 1)
        for page in self.pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page + '?page=2')
                self.assertEqual(
                    list(response.context.get('page_obj').object_list),
                    PaginatorTests.posts[expected_len::-1])


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.posts = Post.objects.bulk_create([
            Post(pk=num,
                 text=f'Тестовый пост {num}',
                 author=user,
                 ) for num in range(13)
        ])
        for post in cls.posts:
            post.pub_date = timezone.now() + datetime.timedelta(days=post.pk)
        Post.objects.bulk_update(cls.posts, ['pub_date'])

    def setUp(self):
        self.guest_client = Client()
        response = self.guest_client.get(REVERSE_CASH.get('posts:index'))
        self.expected_content = response.content

    def test_first_index_page_cache(self):
        """Проверяем, что кеширование первой страницы index работает."""
        CacheTests.posts[-1].delete()
        response = self.guest_client.get(REVERSE_CASH.get('posts:index'))
        self.assertEqual(response.content, self.expected_content)
        cache.clear()
        response = self.guest_client.get(REVERSE_CASH.get('posts:index'))
        self.assertNotEqual(response.content, self.expected_content)

    def test_second_index_page_cache(self):
        """Проверяем, что на второй странице не выводится кеш первой."""
        response = self.guest_client.get(
            REVERSE_CASH.get('posts:index') + '?page=2')
        self.assertNotEqual(response.content, self.expected_content)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreatePostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            image=UPLOADED_IMAGE,
            author=cls.user,
        )
        cls.comment = cls.post.comments.create(
            author=cls.user,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(CreatePostTests.user)

    def test_new_post_exist_on_the_pages(self):
        """Проверяем, что на всех страницах опубликован новый пост
        и комментарий к нему."""
        pages = [
            REVERSE_CASH.get('posts:index'),
            REVERSE_CASH.get('posts:group_list.test_kwargs'),
            REVERSE_CASH.get('posts:profile.test_kwargs'),
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertEqual(
                    response.context.get('page_obj').object_list[0],
                    CreatePostTests.post)
        response = self.auth_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': CreatePostTests.post.pk})
        )
        self.assertEqual(response.context.get('post'), CreatePostTests.post)
        self.assertEqual(response.context.get('post').comments.count(), 1)
        self.assertTrue(response.context.get('post').comments.filter(
            text='Тестовый комментарий').exists())

    def test_new_post_not_exist_on_the_other_pages(self):
        """Проверяем, что пост не отображается там, где не должен."""
        user_without_posts = User.objects.create_user(username='reader')
        group_empty = Group.objects.create(
            title='Пустая тестовая группа',
            slug='test-slug-empty',
            description='Тестовое описание пустой тестовой группы',
        )
        pages = [
            reverse('posts:group_list',
                    kwargs={'slug': group_empty.slug}),
            reverse('posts:profile',
                    kwargs={'username': user_without_posts.username}),
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertEqual(
                    len(response.context.get('page_obj').object_list), 0)

    def test_new_comment_not_exist_on_the_other_page(self):
        """Проверяем, что комментарий к посту не отображается там,
        где не должен."""
        post_other = Post.objects.create(
            text='Другой тестовый пост',
            author=CreatePostTests.user,
        )
        response = self.auth_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post_other.pk})
        )
        self.assertEqual(response.context.get('post').comments.count(), 0)
        CreatePostTests.post.comments.create(
            author=CreatePostTests.user,
            text='Тестовый комментарий'
        )
        response = self.auth_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post_other.pk})
        )
        self.assertEqual(response.context.get('post').comments.count(), 0)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.author = User.objects.create_user(username='author')
        cls.rev_cash = {
            'posts:profile.author':
                reverse('posts:profile',
                        kwargs={'username': cls.author}),
            'posts:profile_follow.author':
                reverse('posts:profile_follow',
                        kwargs={'username': cls.author}),
            'posts:profile_unfollow.author':
                reverse('posts:profile_unfollow',
                        kwargs={'username': cls.author}),
        }
        cls.rev_cash.update(REVERSE_CASH)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(FollowTests.user)

    def test_auth_user_can_subscribe(self):
        """Авторизованный пользователь может единожды подписываться
        на других пользователей и удалять их из подписок."""
        amount_follower = FollowTests.user.follower.count()

        # Проверяем, что можно подписаться
        response = self.auth_client.get(
            FollowTests.rev_cash.get('posts:profile_follow.author'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            FollowTests.rev_cash.get('posts:profile.author'))
        self.assertEqual(
            FollowTests.user.follower.count(), amount_follower + 1)
        self.assertTrue(
            FollowTests.user.follower.filter(
                user=FollowTests.user, author=FollowTests.author).exists())

        # Проверяем, что нельзя подписаться второй раз
        self.auth_client.get(
            FollowTests.rev_cash.get('posts:profile_follow.author'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            FollowTests.rev_cash.get('posts:profile.author'))
        self.assertEqual(
            FollowTests.user.follower.count(), amount_follower + 1)

        # Проверяем, что можно отписаться
        response = self.auth_client.get(
            FollowTests.rev_cash.get('posts:profile_unfollow.author'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            FollowTests.rev_cash.get('posts:profile.author'))
        self.assertEqual(FollowTests.user.follower.count(),
                         amount_follower)
        self.assertFalse(
            FollowTests.user.follower.filter(
                user=FollowTests.user, author=FollowTests.author).exists())

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        user_without_follow = User.objects.create_user(username='NewUser')
        user_without_follow_client = Client()
        user_without_follow_client.force_login(user_without_follow)
        Follow.objects.create(
            user=FollowTests.user, author=FollowTests.author)
        post = Post.objects.create(
            text='Тестовый пост', author=FollowTests.author)
        response = self.auth_client.get(
            FollowTests.rev_cash.get('posts:follow_index'))
        self.assertEqual(
            len(response.context.get('page_obj').object_list), 1)
        self.assertEqual(
            response.context.get('page_obj').object_list, [post, ])

        response = user_without_follow_client.get(
            FollowTests.rev_cash.get('posts:follow_index'))
        self.assertEqual(
            len(response.context.get('page_obj').object_list), 0)

    def test_user_cannot_subscribe_to_himself(self):
        """Пользователь не может подписаться на самого себя."""
        amount_follower = FollowTests.user.follower.count()
        response = self.auth_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': FollowTests.user}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            FollowTests.rev_cash.get('posts:profile.test_kwargs'))
        self.assertEqual(
            FollowTests.user.follower.count(), amount_follower)
        self.assertFalse(
            FollowTests.user.follower.filter(
                user=FollowTests.user, author=FollowTests.user).exists())

    def test_guest_cannot_follow_authors(self):
        """Гость не видит страницу с публикациями избранных пользователей
        и не может подписываться/отписываться на/от авторов."""
        follow_index = FollowTests.rev_cash.get('posts:follow_index')
        guest_client = Client()
        # Заходим на страницу с публикациями избранных пользователей
        response = guest_client.get(follow_index)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={follow_index}')

        # Пробуем подписаться
        amount_follower = FollowTests.author.following.count()
        response = guest_client.get(
            FollowTests.rev_cash.get('posts:profile_follow.author'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'{reverse("users:login")}'
            f'?next='
            f'{FollowTests.rev_cash.get("posts:profile_follow.author")}')
        self.assertEqual(
            FollowTests.user.follower.count(), amount_follower)

        # Пробуем отписаться
        response = guest_client.get(
            FollowTests.rev_cash.get('posts:profile_unfollow.author'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'{reverse("users:login")}'
            f'?next='
            f'{FollowTests.rev_cash.get("posts:profile_unfollow.author")}')
        self.assertEqual(FollowTests.user.follower.count(),
                         amount_follower)
