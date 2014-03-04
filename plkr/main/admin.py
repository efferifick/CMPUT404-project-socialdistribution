from django.contrib import admin
from main.models import User,Post,Comment,FriendsList,Category
admin.site.register(User)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(FriendsList)

# Register your models here.
