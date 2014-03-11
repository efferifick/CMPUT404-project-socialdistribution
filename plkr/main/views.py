from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db import IntegrityError
from django.shortcuts import *
import json
from main.models import *

our_host = "http://127.0.0.1:8000/"

# Create your views here.
def index(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)
    if request.user.is_authenticated():
        return redirect(timeline)
    return render_to_response('main/index.html', {}, context)

# API

def author(request, user_id):
    # Get the author information
    #
    context = RequestContext(request)
    author = Author.objects.get(id=user_id)
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
                flist = flist["authors"]
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
            f = FriendRequest.objects.get(user_who_sent_request = user1_id, user_who_received_request = user2_id, accepted = True)
           
    except Exception,e:
        try:
            f = FriendRequest.objects.get(user_who_sent_request = user2_id, user_who_received_request = user1_id, accepted = True)
        except:
            resp = False

    return resp

def posts(request, post_id):
    context = RequestContext(request)
    try:
        post = Post.objects.get(id=post_id)
    except Exception, e:
        print e
        post = {}

    if request.method == 'POST' or request.method == 'GET':
        #return the post
        #print(post.json())
        return HttpResponse(json.dumps(post.json()), content_type="application/json")
    
    elif request.method == 'PUT':
        body = json.loads(request.body)

        print 'body: '
        print body
        print 'type: '
        print type(body)

        if post == {}:
            post = Post(id=post_id)

        author = Author.objects.get(id=body["author"]["id"])
        post.author = author

        for key, value in body.iteritems():
            if key == "title":
                post.title = value
            elif key == "source":
                post.source = value
            elif key == "origin":
                post.origin = value
            elif key == "description":
                post.description = value
            elif key == "content-type":
                post.contentType = value
            elif key == "content":
                post.content = value
            #elif key == "author":
                #post.author = value
            elif key == "categories":
                post.categories = value
            elif key == "comments":
                post.comments = value
            elif key == "pubDate":
                post.pubDate = value
            elif key == "guid":
                post.guid = value
            elif key == "visibility":
                post.visibility = value
            
        post.save()

        print post.origin

    return None

def get_author_posts(request, user_id):
    # Get the all posts by the user
    #
    context = RequestContext(request)
    
    return None 

def friendrequest(request):
    context = RequestContext(request)

    if request.method == 'POST':
        try:
            print (request.body)
            frequest = json.loads(request.body)  

            friend = frequest["friend"]
            friend = friend["author"]
            author = frequest["author"]

            u_friend = Author.objects.get(id=friend["id"])

            flist = FriendRequest(user_who_sent_request=author["id"], user_who_received_request=u_friend,accepted=False)
            flist.save()

        except Exception, e:
            print(e)
            frequest = {}

    return HttpResponse(json.dumps(frequest), content_type="application/json")


# Site

def register(request):
    context = RequestContext(request)

    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        displayName = request.POST['displayName']
        error = False

        if email is None or email == '':
            # Set error
            messages.error(request, 'Email is required.')
            error = True

        if username is None or username == '':
            # Set error
            messages.error(request, 'Username is required.')
            error = True

        if password is None or password == '':
            # Set error
            messages.error(request, 'Password is required.')
            error = True

        if displayName is None or displayName == '':
            # Set error
            messages.error(request, 'Display Name is required.')
            error = True

        if not error:
            try:
                # Create a User wiith its username, email and password
                user = User.objects.create_user(username, email, password)
                # Users start as inactive so the admin can activate them
                user.is_active = False

                # Create the Author and set the user and display name
                author = Author.create(user, displayName)

                # Save the User first
                user.save()
                # Save the Author last
                author.save()

                # Add a success flash message
                messages.info(request, "Registration complete! Your account now needs to be approved by the administrator.")

                # Send the user to the login screen
                return redirect('django.contrib.auth.views.login')
            except IntegrityError, e:
                if "username" in e.message:
                    # Add the username error
                    messages.error(request, "Username is already taken.")
                elif "email" in e.message:
                    # Add the email error
                    messages.error(request, "An account is associated to that email.")
                else:
                    # Add the generic error
                    messages.error(request, e.message)
            except Exception, e:
                # Add the generic error
                messages.error(request, e.message)

    return render_to_response('main/register.html', {}, context)

def timeline(request):
    context = RequestContext(request)
    # TODO We have to build a function to get the user's stream
    posts = Post.objects.all()
    return render_to_response('main/timeline.html', {'posts': posts}, context)

def profile(request):
    '''
    This function returns the profile for the currently logged in user
    '''
    context = RequestContext(request)
    author = request.user.author
    posts = Post.objects.filter(author=author)
    return render_to_response('main/profile.html', {'posts' : posts}, context)


def editProfile(request):
    context = RequestContext(request)
    author = Author.objects.get(user = request.user)
    authorid = author.id

    if request.method == "POST":
        #Its a post, so we should update the user
        
        author.displayname = request.POST.get('displayname')

        request.user.username = request.POST.get('username')
        request.user.email = request.POST.get('email')
        request.user.save()
        author.save()
    else:
        #Its a get, we should return the information as a html page with a 'save' button
        pass

    return render_to_response('main/editProfile.html', {'username' : request.user.username, 'email' : request.user.email, 'author' : author.json()}, context)

def notfound(request):
    context = RequestContext(request)
    return render_to_response('404.html', {}, context)
