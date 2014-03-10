from django.conf.urls import patterns, include, url
from main import views

urlpatterns = patterns('',
		url(r'^$', 'main.views.index', name='index'),

		# API URLs
		
		# Author - Specific one
		url(r'^author/(?P<user_id>\w+)$', 'main.views.author', name='get_author'),
		#url(r'^author/post/(?P<post_id>\w+)$', views.get_author_post, name='authors_posts'),
		
		# Friends - Of an author
		url(r'^friends/(?P<user1_id>\w+)$', 'main.views.friends', name='get_friends'),
		# Friends - Check friendship
		url(r'^friends/(?P<user1_id>\w+)/(?P<user2_id>\w+)$', 'main.views.friends', name='are_friends'),
		# Friends - Send request
		url(r'^friendrequest$', 'main.views.friendrequest', name='friendrequest'),
		
		# Posts - Specific one
		url(r'^post/(?P<post_id>\w+)$', 'main.views.posts', name='posts'),
		
		# Session - Login
		url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'main/login.html'}),
		# Session - Logout
		url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': 'index'}),

		# Timeline
		url(r'^site/$', 'main.views.timeline', name='timeline'),

		# 404 Error
		url(r'^.*$', 'main.views.notfound', name='notfound'),
		)
