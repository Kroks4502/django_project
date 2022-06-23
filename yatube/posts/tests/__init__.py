from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

TEST_GROUP_SLUG = 'test-slug'
TEST_USERNAME_AUTH = 'auth'

urls = (
    ('posts:index', {}),
    ('posts:follow_index', {}),
    ('posts:group_detail', {}),
    ('posts:post_create', {}),
    ('posts:group_list', {'kwargs': {'slug': TEST_GROUP_SLUG}}),
    ('posts:profile', {'kwargs': {'username': TEST_USERNAME_AUTH}},)
)

REVERSE_CASH = {}
for args in urls:
    key = args[0] if not args[1] else f'{args[0]}.test_kwargs'
    REVERSE_CASH[key] = reverse(args[0], **args[1])

UPLOADED_IMAGE = SimpleUploadedFile(
    name='small.gif',
    content=(b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'),
    content_type='image/gif'
)

DISABLE_CACHING = {
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
}
