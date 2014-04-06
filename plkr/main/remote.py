from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from main.models import *
import datetime, dateutil.parser, json, requests

class RemoteApi:
	TIMEOUT = 1.5
	HEADERS = {"accept": "application/json"}
	
	@classmethod
	def get_author_url(cls, host, author_id):
		return host.get_url() + settings.API_GET_AUTHOR % {'author_id':author_id}

	@classmethod
	def get_author_posts_url(cls, host, author_id):
		return host.get_url() + settings.API_GET_AUTHOR_POSTS % {'author_id':author_id}

	@classmethod
	def get_post_url(cls, host, post_id):
		return host.get_url() + settings.API_GET_POST % {'post_id':post_id}

	@classmethod
	def author_has_friends_url(cls, host, author_id):
		return host.get_url() + settings.API_AUTHOR_HAS_FRIENDS % {'author_id':author_id}

	@classmethod
	def authors_are_friends_url(cls, host, author_id, friend_id):
		return host.get_url() + settings.API_AUTHORS_ARE_FRIENDS % {'author_id':author_id, 'friend_id':friend_id}

	@classmethod
	def send_friend_request_url(cls, host):
		return host.get_url() + settings.API_SEND_FRIENDREQUEST

	@classmethod
	def search_url(cls, host):
		return host.get_url() + settings.API_SEARCH

	@classmethod
	def get_author(cls, host_id, author_id):
		'''
		Returns a tuple with the host and author
		'''
		
		# Default error
		error = (None, None)

		# Validate the host
		if host_id is None:
			return error

		# Validate the author
		if author_id is None:
			return error

		try:
			# Get the host from the database
			host = Host.objects.get(pk=host_id)

			# Get the author from the database
			author = Author.objects.get(pk=author_id, host=host)

			# Return the tuple
			return (host, author)

		except Host.DoesNotExist, e:
			# If the author does not exist, return error
			return error
		except Author.DoesNotExist, e:
			# If the author does not exist, we'll try to retrieve it
			pass
		except Exception, e:
			return error

		try:
			# Generate the URL
			url = cls.get_author_url(host, author_id)

			# Query the URL
			response = requests.get(url, headers=cls.HEADERS, timeout=cls.TIMEOUT)
			
			# Parse the response
			data = response.json()

			# Import the author
			author = Author.objects.create(id=data["id"], displayName=data["displayname"], host=host)

			# Return the tuple
			return (host, author)

		except Exception, e:
			return error

	@classmethod
	def get_author_posts(cls, author, viewer):
		'''
		Returns a list of remote author posts that a viewer can access
		'''

		# Initialize the results
		posts = []

		# Generate the URL
		url = cls.get_author_posts_url(author.host, author.id)

		# Generate the viewer id parameter
		viewer_id = viewer.id if viewer is not None else None

		# TODO Test this

		try:
			# Query the URL
			response = requests.get(url, params=dict(id=viewer_id), headers=cls.HEADERS, timeout=cls.TIMEOUT)

			# Parse the response
			data = response.json()

			# Add the post to the result list
			for post_data in data["posts"]:
				try:
					post = Post()
					post.title = post_data["title"]
					post.source = post_data["source"] if "source" in post_data else cls.get_post_url(author.host, post_data["guid"])
					post.origin = post_data["origin"]
					post.description = post_data["description"]
					post.contentType = post_data["content-type"]
					post.content = post_data["content"]
					post.author = author
					# TODO To add this we need to save the post. Do we want to though?
					# post.categories = [Category(name=c) for c in post_data["categories"]]
					# post.comments = [Comment(author=Author(id=com["author"]["id"], displayName=com["author"]["displayname"], host=author.host), pubDate=dateutil.parser.parse(com["pubDate"]),comment=com["comment"],post=post) for com in post_data["comments"]]
					post.pubDate = dateutil.parser.parse(post_data["pubDate"])
					post.id = post_data["guid"]
					post.visibility = post_data["visibility"]
					posts.append(post)

				except Exception, e:
					pass

		except Exception, e:
			pass

		return posts

	@classmethod
	def get_search_results(cls, query):
		'''
		Returns a list of remote authors that match a search query
		'''

		# Initialize the results
		authors = []

		# Get all the remote hosts
		hosts = Host.objects.filter(is_local=False)

		# Query remote hosts
		for host in hosts:
			try:
				# Search the remote host
				response = requests.get(cls.search_url(host), params=dict(query=query), headers=cls.HEADERS, timeout=cls.TIMEOUT)

				# Parse the response
				data = response.json()

				# Add the author to the result list
				for author_data in data:
					remote_author = Author()
					remote_author.id = author_data['id']
					remote_author.host = host
					remote_author.displayName = author_data['displayname']
					authors.append(remote_author)

			except Exception, e:
				# If there's an exception, just catch it
				print('Querying %s failed, query: "%s"' % (cls.search_url(host), query))

		# Return the search results
		return authors

	@classmethod
	def author_is_friends_with(author, friends):
		'''
		Determine if an author is friends with a group of authors
		'''

		# TODO Implement this
		