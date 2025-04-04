from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone

from .models import Post


def paginate_queryset(request, queryset, per_page=settings.LIMIT_POST):
    return Paginator(queryset, per_page).get_page(request.GET.get('page'))


def get_posts(
    posts=Post.objects,
    apply_filtering=True,
    apply_annotation=True
):
    posts = posts.select_related('category', 'location', 'author')

    if apply_filtering:
        posts = posts.filter(
            is_published=True,
            pub_date__lt=timezone.now(),
            category__is_published=True
        )

    if apply_annotation:
        posts = posts.annotate(
            comment_count=Count('comments')
        )

    return posts.order_by(*Post._meta.ordering)
