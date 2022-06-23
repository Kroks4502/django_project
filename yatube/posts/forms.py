from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image', )
        help_texts = {
            'text': _('Текст вашей публикации'),
            'group': _('Выберите группу (необязательно)'),
            'image': _('Выберите изображение (необязательно)'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': _('Текст вашего комментария'),
        }
