from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView


from .forms import CommentCreateForm, PostForm, UserEditForm
from .models import Category, Comment, Post
from .auxiliary import paginate_queryset, get_posts


User = get_user_model()


class RegistrationView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('pages:homepage')


class UserProfileView(ListView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = settings.LIMIT_POST

    def get_profile(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        profile = self.get_profile()
        return get_posts(
            profile.posts.all(),
            apply_filtering=self.request.user != profile,
            apply_annotation=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_profile()
        return context


@login_required
def edit_profile(request):
    form = UserEditForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)
    return render(request, 'blog/user.html', {'form': form, })


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    success_url = reverse_lazy('blog:index')

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    model = Post
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        base_queryset = get_posts(Post.objects.all(), apply_filtering=False, apply_annotation=False)
        post = get_object_or_404(base_queryset, pk=self.kwargs['post_id'])

        if post.author != self.request.user:
            post = get_object_or_404(
                get_posts(Post.objects.all(), apply_annotation=False),
                pk=post.pk
            )

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('author')
        context['form'] = CommentCreateForm()
        return context


class PostListView(ListView):
    model = Post
    paginate_by = settings.LIMIT_POST
    template_name = 'blog/index.html'
    queryset = get_posts()


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = settings.LIMIT_POST

    def fetch_category(self):
        category_slug = self.kwargs['category_slug']
        return get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )

    def get_queryset(self):
        category = self.fetch_category()
        return get_posts(category.posts)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.fetch_category()
        return context


@login_required()
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id)

    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)

    return render(request, 'blog/create.html', {
        'form': form,
        'post': post,
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', request.user.username)

    return render(request, 'blog/create.html', {
        'post': post,
        'form': PostForm(instance=post),
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    form = CommentCreateForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = CommentCreateForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
    })
