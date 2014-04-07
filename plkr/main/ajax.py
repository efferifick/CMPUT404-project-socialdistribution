import dateutil.parser
import json
from dajaxice.decorators import dajaxice_register
from django.template.loader import render_to_string
from django.template import RequestContext
from main.models import *

@dajaxice_register(method='GET', name='author.get_new_posts')
def get_new_posts(request, date, author_id):
	context = RequestContext(request)

	# Initialize response
	response = []

	# Initialize posts array
	posts = []

	# Parse the date
	date = dateutil.parser.parse(date)

	# Determine the viewer
	viewer = request.user.author if request.user.is_authenticated() else None

	# If it's a timeline request
	if author_id is None:
		# If the user is logged in
		if viewer is not None:
			# Grab the author's timeline posts
			posts = viewer.get_timeline_posts()
	else:
		# Otherwise, it's a profile request
		
		try:
			# Grab the author (profile owner)
			author = Author.objects.get(pk=author_id)

			# Get the author's posts viewable to the viewer
			posts = author.get_posts_viewable_by(viewer)
		except Exception, e:
			pass

	# Filter by the date
	posts = [post for post in posts if post.pubDate > date]

	# Render the posts
	for post in posts:
		response.append(render_to_string('main/post.html', {'post': post}, context))

	# Send the response
	return json.dumps(response)
