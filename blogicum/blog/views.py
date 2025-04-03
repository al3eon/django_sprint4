from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from .forms import CommentCreateForm, PostForm, UserEditForm
from .models import Category, Comment, Post

LIMIT_POST = 10
POST_ORDERING = ('-pub_date',)

User = get_user_model()


def paginate_queryset(request, queryset, per_page=LIMIT_POST):
    return Paginator(queryset, per_page).get_page(request.GET.get('page'))


def get_post(
    posts=Post.objects.all(),
    use_filtering=True,
    use_select_related=True,
    use_annotation=True
):
    if use_filtering:
        posts = posts.filter(
            is_published=True,
            pub_date__lt=timezone.now(),
            category__is_published=True
        )

    if use_select_related:
        posts = posts.select_related('category', 'location', 'author')

    if use_annotation:
        posts = posts.annotate(
            comment_count=Count('comments')
        )
    return posts.order_by(*POST_ORDERING)


class AuthorMixin(UserPassesTestMixin):
    def test_func(self):
        target_object = self.get_object()
        return target_object.author == self.request.user


class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_visible_posts(self):
        """Возвращает посты, видимые текущему пользователю"""
        user = self.object
        return get_post(
            posts=user.posts.all(),
            use_filtering=self.request.user != user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_obj'] = paginate_queryset(
            self.request,
            self.get_visible_posts()
        )
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
        post = super().get_object(queryset)

        if post.author == self.request.user:
            return post

        published_posts = get_post(
            Post.objects.all(),
            use_select_related=False,
            use_annotation=False
        )
        return get_object_or_404(published_posts, pk=post.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['form'] = CommentCreateForm()
        return context


class PostListView(ListView):
    model = Post
    paginate_by = LIMIT_POST
    template_name = 'blog/index.html'
    queryset = get_post()


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = LIMIT_POST

    def fetch_category(self):
        category_slug = self.kwargs['category_slug']
        return get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )

    def get_queryset(self):
        category = self.fetch_category()
        return get_post(category.posts)

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
    comment = get_object_or_404(Comment, id=comment_id)

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
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
    })
