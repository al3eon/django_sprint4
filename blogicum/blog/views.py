from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView

from .models import Category, Post

LIMIT_POST = 5

User = get_user_model()

class UserProfileView(DetailView):
    model = User
    # template_name = 'blog/profile.html'  # Используем существующий шаблон
    # context_object_name = 'profile'  # Как в вашем шаблоне!
    # slug_field = 'username'  # Ищем пользователя по полю username
    # slug_url_kwarg = 'username'  # Как назван параметр в URL

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    fields = [
        'title',
        'text',
        'pub_date',
        'location',
        'category'
    ]

    def form_valid(self, form):
        # Автоматически назначаем автора = текущему пользователю
        form.instance.author = self.request.user

        # Если pub_date не указана, ставим текущее время
        if not form.cleaned_data['pub_date']:
            form.instance.pub_date = timezone.now()

        return super().form_valid(form)

class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'  # Используем существующий шаблон
    context_object_name = 'profile'  # Как в вашем шаблоне!
    slug_field = 'username'  # Ищем пользователя по полю username
    slug_url_kwarg = 'username'  # Как назван параметр в URL

class PostListView(ListView):
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    queryset = Post.objects.select_related(
        'location',
        'category',
        'author'
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )[:LIMIT_POST]


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related(
            'location',
            'category',
            'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )


class CategoryPostsView(ListView):
    template_name = 'blog/category.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.select_related(
            'location',
            'category',
            'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category=category
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context