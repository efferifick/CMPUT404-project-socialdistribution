from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from main.models import *
import datetime, dateutil.parser, json, requests

class RemoteApi:
	TIMEOUT = 1.5
	HEADERS = {"accept": "application/json", "content-type": "application/json"}
	
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
	def get_public_posts_url(cls, host):
		return host.get_url() + settings.API_GET_PUBLIC_POSTS

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
	def import_post(cls, author, host, post_data):
		post = Post()
		if "github" in post_data["origin"]:
			post.gitHub = True
		post.title = post_data["title"]
		post.source = post_data["source"]
		post.origin = post_data["origin"]
		post.description = post_data["description"]
		post.contentType = post_data["content-type"]
		post.content = post_data["content"]
		
		if author is None:
			host, author = cls.get_author(host.id, post_data["author"]["id"])
		
		post.author = author

		post.pubDate = dateutil.parser.parse(post_data["pubDate"])
		post.id = post_data["guid"]
		post.visibility = post_data["visibility"]
		post.save()

		# Now that the post exists, add the categories
		for category_name in post_data["categories"]:
			try:
				category = Category.objects.get(name=category_name)
			except ObjectDoesNotExist, e:
				category = Category.objects.create(name=category_name)

			post.categories.add(category)

		# Remove all the existing comments
		Comment.objects.filter(post=post).delete()

		# Now add the comments
		for comment_data in post_data["comments"]:
			try:
				comment_owner = Author.objects.get(pk=comment_data["author"]["id"])
			except ObjectDoesNotExist, e:
				# Try to determine the host of the author commenting
				comment_host = None
				
				# Get all hosts
				hosts = Host.objects.all()
		
				# Test each host using the URL
				for host in hosts:
					if host.get_url() == comment_data["author"]["host"]:
						comment_host = post.author.host
						break

				# If the host could not be found, then just don't try to add the comment
				if comment_host is None:
					break

				# Import the author
				comment_owner = Author.objects.create(id=comment_data["author"]["id"], displayName=comment_data["author"]["displayname"], host=comment_host)

			# Finally, create the comment
			comment = Comment.objects.create(post=post, author=comment_owner, comment=comment_data["comment"], pubDate=dateutil.parser.parse(comment_data["pubDate"]))

		# Save the post again
		post.save()

		return post

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

		try:
			# Query the URL
			response = requests.get(url, params=dict(id=viewer_id), headers=cls.HEADERS, timeout=cls.TIMEOUT)

			# Parse the response
			data = response.json()

			# Add the post to the result list
			for post_data in data["posts"]:
				try:
					# Import the post
					post = cls.import_post(author, author.host, post_data)

					# Append the post
					posts.append(post)

				except Exception, e:
					pass

		except Exception, e:
			print 'Querying %s, error: %s' % (url, e.message)

		return posts

	@classmethod
	def get_public_posts(cls):
		'''
		Returns a list of remote public posts
		'''

		# Initialize the results
		posts = []

		# Get all hosts
		hosts = Host.objects.filter(is_local=False)

		# Get public posts from each remote host
		for host in hosts:
			# Generate the URL
			url = cls.get_public_posts_url(host)

			try:
				# Query the URL
				response = requests.get(url, headers=cls.HEADERS, timeout=cls.TIMEOUT)

				# Parse the response
				data = response.json()

				# Add the post to the result list
				for post_data in data["posts"]:
					try:
						# Import the post
						post = cls.import_post(None, host, post_data)

						# Append the post
						posts.append(post)

					except Exception, e:
						pass

			except Exception, e:
				print 'Querying %s, error: %s' % (url, e.message)

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
					remote_author.save()
					authors.append(remote_author)

			except Exception, e:
				# If there's an exception, just catch it
				print('Querying %s failed, query: "%s"' % (cls.search_url(host), query))

		# Return the search results
		return authors

	@classmethod
	def author_is_friends_with(cls, author, friends):
		'''
		Determine if an author is friends with a group of authors
		'''

		# TODO test this

		try:
			# Determine the params of the request
			params = dict(query='friends', author=author.id, authors=[friend.id for friend in friends])

			# Query the remote host
			response = requests.post(cls.author_has_friends_url(author.host, author.id), params=params, headers=cls.HEADERS, timeout=cls.TIMEOUT)

			# Parse the response
			data = response.json()

			# If the result has at least one friend
			return len(data["friends"]) > 0

		except Exception, e:
			pass

		# Return False by default or in error
		return False

	@classmethod
	def send_friend_request(cls, author, friend, query='friendrequest'):
		'''
		Determine if an author is friends with a group of authors
		'''

		# TODO test this
		
		try:
			# Determine the params of the request
			params = dict(query=query, author=friend.json(), friend=dict(author=author.json()))

			# Query the remote host
			response = requests.post(cls.send_friend_request_url(author.host), data=json.dumps(params), headers=cls.HEADERS, timeout=cls.TIMEOUT)

			# If the response is ok
			return response.status_code == 200

		except Exception, e:
			pass

		# Return False by default or in error
		return False
