from django.apps import apps
from django.contrib.auth import get_user_model


def group_lists(request):
    """"""
    group_model = apps.get_model('posts', 'Group')
    post_model = apps.get_model('posts', 'Post')
    groups = []
    for group in group_model.objects.all():
        if post_model.objects.filter(group__pk=group.pk).count():
            groups.append(group)
    return {
        'menu_group_lists': groups
    }


def author_lists(request):
    """"""
    user_model = get_user_model()
    authors = []
    for user in user_model.objects.all():
        if user.posts.count():
            authors.append({'username': user.username,
                            'full_name': user.get_full_name()})
    return {
        'menu_author_lists': authors
    }
