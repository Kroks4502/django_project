from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.app_url = '/about/'
        self.urls_template = {
            'author/': 'about/author.html',
            'tech/': 'about/tech.html',
        }

    def test_about_url_exists_at_desired_location(self):
        """Проверяем доступность всех адресов."""
        for url in self.urls_template:
            with self.subTest(url=url):
                responce = self.guest_client.get(self.app_url + url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Проверяем корректность шаблонов."""
        for url, template in self.urls_template.items():
            with self.subTest(url=url, template=template):
                responce = self.guest_client.get(self.app_url + url)
                self.assertTemplateUsed(responce, template)


class AboutViewTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.app_url = '/about/'
        self.urls_template = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def test_about_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имен страниц, доступен."""
        for url in self.urls_template:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_uses_correct_template(self):
        """При запросе к страницам применяется ожидаемый шаблон."""
        for url, template in self.urls_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
