from django.contrib import admin
from main.models import Author, Post, Comment, FriendRequest, Category

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(FriendRequest)

# Register your models here.
