from django.contrib import admin

from .models import Category, Location, Post, Comment


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'slug',
        'is_published'
    )
    list_editable = ('is_published',)
    search_fields = ('title', 'description')
    list_filter = ('is_published',)


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('name',)
    list_filter = ('created_at',)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'category',
        'location',
        'pub_date',
        'is_published'
    )
    list_filter = ('category', 'is_published', 'pub_date')
    search_fields = ('title', 'text')
    list_editable = ('is_published',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created_at')
    list_filter = ('created_at', 'author', 'post')
    search_fields = ('text', 'author__username', 'post__title')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
