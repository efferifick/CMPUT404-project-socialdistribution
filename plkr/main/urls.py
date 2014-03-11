from django.conf.urls import patterns, include, url
from main import views

urlpatterns = patterns('',
		url(r'^$', 'main.views.index', name='index'),

		# API URLs
		
		# Author - Specific one
		url(r'^author/(?P<user_id>[a-zA-Z0-9\-]+)$', 'main.views.author', name='get_author'),
		#url(r'^author/post/(?P<post_id>\w+)$', views.get_author_post, name='authors_posts'),
		
		# Friends - Of an author
		url(r'^friends/(?P<user1_id>[a-zA-Z0-9\-]+)$', 'main.views.friends', name='get_friends'),
		# Friends - Check friendship
		url(r'^friends/(?P<user1_id>[a-zA-Z0-9\-]+)/(?P<user2_id>[a-zA-Z0-9\-]+)$', 'main.views.friends', name='are_friends'),
		# Friends - Send request
		url(r'^friendrequest$', 'main.views.friendrequest', name='friendrequest'),
		
		# Posts - Specific one
		url(r'^post/(?P<post_id>[a-zA-Z0-9\-]+)$', 'main.views.posts', name='posts'),
		
		# Auth - Login
		url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'main/login.html'}),
		# Auth - Logout
		url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': 'index'}),
		# Auth - Register
		url(r'^register$', 'main.views.register', name='register'),

		# Timeline
		url(r'^site/$', 'main.views.timeline', name='timeline'),
		
		# Profile
		url(r'^site/profile$', 'main.views.profile', name='profile'),
		url(r'^site/profile/edit$', 'main.views.profileEdit', name='profileEdit'),
		
		# Posts - New
		url(r'^site/posts/new$', 'main.views.postNew', name='postNew'),

		# 404 Error
		url(r'^.*$', 'main.views.notfound', name='notfound'),
		)
