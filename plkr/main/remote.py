from django.conf import settings

class RemoteApi:
	
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