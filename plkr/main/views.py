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

def author(request, user_id):
	# Get the author information
	#
	context = RequestContext(request)
    	author = User.objects.get(id=user_id)
	return HttpResponse(json.dumps(author.json()), content_type="application/json")

def friends(request, user1_id, user2_id = None):
	context = RequestContext(request)
	resp = dict()
	if(user2_id == None):
		#Get the user1 friends
		resp["query"] = "friends"
		resp["author"] = user1_id
		friends = []

		if request.method == 'POST':
			try:
				flist = json.loads(request.body)
				flist = flist["friends"]
				friends = [f for f in flist if are_friends(user1_id, f)]
				resp["friends"] = friends		    
			except Exception, e:
				resp["friends"] = []

	else:
		if are_friends(user1_id, user2_id):
			resp["friends"] = "YES"
		else:
			resp["friends"] = "NO"

		resp["query"] = "friends"
		#resp["friends"] = [user1_id, user2_id] In the spec the key friends is used twice

  	return HttpResponse(json.dumps(resp), content_type="application/json")

def are_friends(user1_id, user2_id):
        # Return if user1 and user2 are friends
	# Check user1's list, if not in this list check on user2's list for 
	# friendship relationship. This is because friendslist strores who 
	# requested the friendship
	resp = True
	try:
	        f = FriendsList.objects.get(user_who_sent_request = user1_id, user_who_received_request = user2_id, accepted = True)
		   
	except Exception,e:
		try:
			f = FriendsList.objects.get(user_who_sent_request = user2_id, user_who_received_request = user1_id, accepted = True)
		except:
			resp = False

	return resp

def posts(request, post_id):
	context = RequestContext(request)
    
	if request.method == 'POST' or request.method == 'GET':
        #return the post
		post = Post.objects.get(id=post_id)
	        print(post.json())
		return HttpResponse(json.dumps(post.json()), content_type="application/json")
	elif request.method == 'PUT':
		pass
        #insert/update the post
    
	return None

def get_author_posts(request, user_id):
	# Get the all posts by the user
	#
	context = RequestContext(request)
    
	return None	

