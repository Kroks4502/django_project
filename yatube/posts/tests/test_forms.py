import shutil
import tempfile

from django.conf import settings
from django.db.models import Max
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, User
from . import REVERSE_CASH, TEST_USERNAME_AUTH, UPLOADED_IMAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostFormTest.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': '',
            'image': UPLOADED_IMAGE
        }
        response = self.auth_client.post(
            REVERSE_CASH.get('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            REVERSE_CASH.get('posts:profile.test_kwargs'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый пост',
            group=None,
            image=f'posts/{UPLOADED_IMAGE.name}').exists())
        last_post_pk = Post.objects.aggregate(pk=Max('pk'))
        last_post = Post.objects.filter(**last_post_pk)
        self.assertEqual(last_post.get().text, 'Тестовый пост')
        last_post_pub_date = Post.objects.aggregate(pub_date=Max('pub_date'))
        last_post = Post.objects.filter(**last_post_pub_date)
        self.assertEqual(last_post.get().text, 'Тестовый пост')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        post = Post.objects.create(
            text='Тестовый пост до редактирования',
            author=PostFormTest.user,
        )
        form_data = {
            'text': 'Тестовый пост после редактирования',
            'group': '',
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.pk}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            pk=post.pk,
            text='Тестовый пост после редактирования',
            group=None,).exists())


class PostCommentsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_USERNAME_AUTH)
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.create_user(username='OtherUser')
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostCommentsTest.user)

    def test_create_new_comment(self):
        """Валидная форма создает новый комментарий."""
        post = PostCommentsTest.post
        amount_comments = post.comments.count()
        response = self.auth_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data={'text': 'Тестовый комментарий'},
            follow=True)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.pk}))
        self.assertEqual(post.comments.count(),
                         amount_comments + 1)
        self.assertTrue(post.comments.filter(
            text='Тестовый комментарий'
        ).exists())

    def test_guest_can_not_create_comment(self):
        """Проверяем, что гость не может оставить комментарий."""
        post = PostCommentsTest.post
        amount_comments = post.comments.count()
        guest_client = Client()
        response = guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': post.pk}),
            data={'text': 'Тестовый комментарий гостя'},
            follow=True)
        self.assertRedirects(
            response,
            reverse('users:login')
            + f'?next=/posts/{post.pk}/comment/')
        self.assertEqual(post.comments.count(),
                         amount_comments)
