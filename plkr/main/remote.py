from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from main.models import *
import datetime, json, requests

class RemoteApi:
	TIMEOUT = 0.3
	
	@classmethod
	def get_author_url(cls):
		return settings.API_GET_AUTHOR

	@classmethod
	def get_author_posts_url(cls):
		return settings.API_GET_AUTHOR_POSTS

	@classmethod
	def get_post_url(cls):
		return settings.API_GET_POST

	@classmethod
	def author_has_friends_url(cls):
		return settings.API_AUTHOR_HAS_FRIENDS

	@classmethod
	def authors_are_friends_url(cls):
		return settings.API_AUTHORS_ARE_FRIENDS

	@classmethod
	def send_friend_request_url(cls):
		return settings.API_SEND_FRIENDREQUEST

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
			host = Host.object.get(pk=host_id)

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
			url = "%author/%s" % (host.get_(), author_id)

			# Query the URL
			response = requests.get(url, params=dict(query=query), timeout=cls.TIMEOUT)

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

		#TODO implement
		return []