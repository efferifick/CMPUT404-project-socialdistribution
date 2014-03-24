from django.conf.urls import patterns, include, url
from main import views

urlpatterns = patterns('',
		# API URLs
		
		# Author - Specific one
		url(r'^author/(?P<user_id>[a-zA-Z0-9\-]+)$', 'main.views.api_get_author', name='api_get_author'),
		# Author - Posts by an author
		#url(r'^author/(?P<post_id>\w+)/posts$', views.get_author_post, name='authors_posts'),
		
		# Friends - Author has these friends?
		url(r'^friends/(?P<user1_id>[a-zA-Z0-9\-]+)$', 'main.views.api_author_has_friends', name='api_author_has_friends'),
		# Friends - Check friendship
		url(r'^friends/(?P<user1_id>[a-zA-Z0-9\-]+)/(?P<user2_id>[a-zA-Z0-9\-]+)$', 'main.views.api_authors_are_friends', name='api_authors_are_friends'),
		# Friends - Send request
		url(r'^friendrequest$', 'main.views.api_send_friendrequest', name='api_send_friendrequest'),

		# Posts - Specific one
		url(r'^post/(?P<post_id>[a-zA-Z0-9\-]+)$', 'main.views.api_get_post', name='api_get_post'),
		
		# Site
		
		# Homepage
		url(r'^$', 'main.views.index', name='index'),

		# Auth - Login
		url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'main/login.html'}),
		# Auth - Logout
		url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': 'index'}),
		# Auth - Register
		url(r'^register$', 'main.views.register', name='register'),

		# Timeline
		url(r'^site/$', 'main.views.timeline', name='timeline'),
		
		# Profile - View
		url(r'^site/profile$', 'main.views.profile', name='profile'),
		# Profile - Edit
		url(r'^site/profile/edit$', 'main.views.profile_edit', name='profile_edit'),
		# Profile - Author profile
		url(r'^site/profile/(?P<username>[a-zA-Z0-9]+)$', 'main.views.profile_author', name='profile_author'),

		# Friends
		url(r'^site/friends$', 'main.views.friends', name='friends'),
		# Friends - Accept friendship
		url(r'^site/friends/accept$', 'main.views.accept_friendship', name='accept_friendship'),
		# Friends - Remove friendship
		url(r'^site/friends/remove$', 'main.views.remove_friendship', name='remove_friendship'),
		# Friends - Request friendship
		url(r'^site/friends/new$', 'main.views.request_friendship', name='request_friendship'),
		
		# Posts - New
		url(r'^site/posts/new$', 'main.views.post_new', name='post_new'),
		# Posts - View
		url(r'^site/posts/(?P<post_id>[a-zA-Z0-9\-]+)$', 'main.views.post', name='post'),
		# Posts - Delete
		url(r'^site/posts/(?P<post_id>[a-zA-Z0-9\-]+)/delete$', 'main.views.post_delete', name='post_delete'),
		# Posts - Comment
		url(r'^site/posts/(?P<post_id>[a-zA-Z0-9\-]+)/comment$', 'main.views.post_comment', name='post_comment'),
		)
