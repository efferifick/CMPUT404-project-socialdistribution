from django.shortcuts import *
from django.core import serializers
#render, RequestContext
import json
from main.models import *

# Create your views here.
def index(request):
	# Request the context of the request.
	# The context contains information such as the client's machine details, for example.
	context = RequestContext(request)
    
	return None

def get_author(request, user_id):
	# Get the author information
	#
	context = RequestContext(request)
    	author = User.objects.get(id=user_id)
	print("hello")
	print(author.json())
	return HttpResponse(json.dumps(author.json()), content_type="application/json")

def get_friends(request, user_id):
	# Get the user friends
	#
	context = RequestContext(request)
    
	return None

def are_friends(request, user1_id, user2_id):
	# Return if the user1 and user2 are friends
	#
	context = RequestContext(request)
    
	return None

def posts(request, post_id):
	context = RequestContext(request)
    
	if request.method == 'POST' or request.method == 'GET':
		pass
        #return the post
	elif request.method == 'PUT':
		pass
        #insert/update the post
    
	return None

def get_author_posts(request, user_id):
	# Get the all posts by the user
	#
	context = RequestContext(request)
    
	return None	

