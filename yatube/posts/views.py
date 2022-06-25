import os.path
import random

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User
from .settings import DEFAULT_AMOUNT_POSTS_ON_PAGE


def render_page_with_paginator(request: WSGIRequest,
                               template: str,
                               post_list: QuerySet,
                               additional_context: dict = None) -> render:
    """
    Вызывает рендеринг объектов с шаблоном с применением паджинатора.

    Args:
        request: Запрос
        template: Адрес шаблона
        post_list: Все объекты
        additional_context: Дополнительный контекст
    Returns:
        Функция render
    """
    paginator = Paginator(post_list, DEFAULT_AMOUNT_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, }
    if additional_context:
        context.update(additional_context)
    return render(request, template, context)


def index(request):
    template = 'posts/index.html'
    page_name = 'Последние обновления на сайте'

    post_list = Post.objects.all()
    posts_with_img = []
    for post in post_list:
        if post.image:
            posts_with_img.append(post)
        if len(posts_with_img) == 3:
            break
    additional_context = {'page_name': page_name,
                          'posts_with_img': posts_with_img}

    return render_page_with_paginator(request, template,
                                      post_list, additional_context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'

    additional_context = {'group': group, }
    post_list = group.groups.all()

    return render_page_with_paginator(request, template,
                                      post_list, additional_context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'

    post_list = author.posts.all()
    following = request.user.follower.filter(
        author=author).exists() if request.user.is_authenticated else False
    additional_context = {'author': author,
                          'following': following, }

    return render_page_with_paginator(request, template,
                                      post_list, additional_context)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    page_name = 'Публикации избранных авторов'

    following = request.user.follower.values_list('author')
    post_list = Post.objects.filter(author__pk__in=following)
    additional_context = {'page_name': page_name, }

    return render_page_with_paginator(request, template,
                                      post_list, additional_context)


def group_detail(request):
    template = 'posts/group_detail.html'
    return render(request, template)


def groups(request):
    template = 'posts/groups.html'
    page_name = 'Список групп'
    groups_ = Group.objects.all()
    context = {'page_name': page_name,
               'groups': groups_, }
    return render(request, template, context)


def authors(request):
    template = 'posts/authors.html'
    page_name = 'Список авторов'
    authors_ = User.objects.all()
    context = {'page_name': page_name,
               'authors': authors_, }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/post_detail.html'
    form = CommentForm()
    context = {'post': post,
               'form': form, }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None, )
    if request.method == 'POST' and form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)

    context = {'form': form, }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    template = 'posts/create_post.html'
    context = {'post': post,
               'form': form,
               'is_edit': True, }
    return render(request, template, context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    post.delete()
    return redirect('posts:profile', username=post.author)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        request.user.follower.get_or_create(author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    request.user.follower.filter(author__username=username).delete()
    return redirect('posts:profile', username=username)
