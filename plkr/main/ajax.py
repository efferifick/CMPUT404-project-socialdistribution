import json
import dateutil.parser
from main.models import *
from django.template.loader import render_to_string
from django.template import RequestContext
from views import timeline_posts
from dajaxice.decorators import dajaxice_register

@dajaxice_register(method='GET')
def get_new_posts(request, date):
    context = RequestContext(request)
    posts = timeline_posts(request)
    latestPostDate = dateutil.parser.parse(date)

    posts = [post for post in posts if post.pubDate > latestPostDate]
    
    response = []
    if posts:
    	for post in posts:
	    response.append(render_to_string('main/post.html', {'post': post}, context))

    return json.dumps(response)
