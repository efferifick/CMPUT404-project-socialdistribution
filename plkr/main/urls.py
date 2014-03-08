from django.conf.urls import patterns, include, url
from main import views

urlpatterns = patterns('',
		url(r'^$', views.index, name="index" ),
		#authors path
		url(r'^author/(?P<user_id>\w+)/$', views.author, name="get_author"),
		#url(r'^author/post/(?P<post_id>\w+)/$', views.get_author_post,
		#	name="authors_posts"),
		#friends path
		url(r'^friends/(?P<user1_id>\w+)/$', views.friends,
			name="get_friends"),
		url(r'^friends/(?P<user1_id>\w+)/(?P<user2_id>\w+)/$',
			views.friends, name="are_friends"),
		#post path
		url(r'^post/(?P<post_id>\w+)/$', views.posts, name="posts"),
		#friend request
		url(r'^friendrequest/$', views.friendrequest, name="friendrequest"),
		)
