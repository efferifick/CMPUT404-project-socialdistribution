from HTMLParser import HTMLParser
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import *
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
from main.models import *
from main.remote import RemoteApi
import cgi, datetime, json, dateutil.parser, os.path, requests, urllib, hashlib, pytz, re

# API

def api_send_json(obj):
    '''
    This function returns the http response to send a serialized object to the client, in json format
    '''
    return HttpResponse(json.dumps(obj, indent=4), content_type="application/json")

def api_send_error(message, status=400):
    '''
    This function returns the http response for errors (sending status 400 as it's always the user's fault)
    '''
    return HttpResponse(json.dumps(dict(error=True, message=message)), content_type="application/json", status=status)

def api_validate_client(request):
    # Determine the remote client address
    client_address = get_ip(request)

    # Create the error response
    response = api_send_error("Client is not authorized to use this API.", 403)

    # Validate the remote client address
    if client_address is None:
        return (False, response)
    else:
        try:
            client = Host.objects.get(ip_address=client_address)

            return (True, client)
        except ObjectDoesNotExist, e:
            return (False, response)
        except Exception, e:
            return (False, response)

def api_get_viewer(request):
    # Check if viewer data was supplied
    if "id" in request.GET.keys():
        # Get the viewer id
        viewer_id = request.GET["id"]
        
        try:
            # Check if the viewer exists in our database
            return Author.objects.get(pk=viewer_id)
        except ObjectDoesNotExist, e:
            # Assuming no viewer
            return None
    else:
        # Assuming no viewer
        return None

@csrf_exempt
def api_get_author(request, user_id):
    '''
    This view handles api requests for author data
    '''
    
    # Validate the request method
    if request.method != 'GET':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # Get the author information
        author = Author.objects.get(id=user_id)

        # Send the author data
        return api_send_json(author.json())

    except ObjectDoesNotExist, e:
        return api_send_error("Author does not exist.", 404)
    except Exception, e:
        return api_send_error(e.message, 500)

@csrf_exempt
def api_author_has_friends(request, user1_id):
    '''
    This view handles api requests for author friendships
    '''
    
    # Validate the request method
    if request.method != 'POST':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    # Prepare the response
    resp = dict()
    resp["query"] = "friends"
    resp["author"] = user1_id
    
    try:
        # Load request data
        flist = json.loads(request.body)

        # Validate request
        if "authors" not in flist:
            return api_send_error("Missing authors data in request.", 400)

        # Get the authors
        flist = flist["authors"]

        # Filter only those that are friends with the author
        friends = [f for f in flist if Author.are_friends(user1_id, f)]

        # Add the friends to the response
        resp["friends"] = friends

        # Send the response
        return api_send_json(resp)

    except Exception, e:
        return api_send_error("Missing authors data in request.", 400)

@csrf_exempt
def api_authors_are_friends(request, user1_id, user2_id):
    '''
    This view handles api requests for friendships
    '''
    
    # Validate the request method
    if request.method != 'GET':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    # Prepare the response
    resp = dict()
    resp["query"] = "friends"

    try:
        if Author.are_friends(user1_id, user2_id):
            resp["friends"] = "YES"
        else:
            resp["friends"] = "NO"

        # Send the response
        return api_send_json(resp)
    except Exception, e:
        return api_send_error(e.message, 500)

@csrf_exempt
def api_get_post(request, post_id):
    '''
    This view handles api requests for post data
    '''
    
    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        post = Post.objects.get(id=post_id)
    except ObjectDoesNotExist, e:
        post = None
    except Exception, e:
        return api_send_error(e.message, 500)

    try:
        # If it's a GET or a POST, send the post
        if request.method == 'POST' or request.method == 'GET':
            # If the post was not found
            if post is None:
                # Return not found error
                return api_send_error("Post does not exist.", 404)
            else:
                # Get the viewer
                viewer = api_get_viewer(request)

                # If the post can be viewed by the viewer
                if post.can_be_viewed_by(viewer):
                    # Return the post data
                    return api_send_json(dict(posts=[post.json()]))
                else:
                    # Otherwise, return the error (unauthorized)
                    return api_send_error("Unauthorized to view this post.", 401)
        
        # Only PUT is allowed from here on
        if request.method != 'PUT':
            return api_send_error("Method not allowed.", 405)

        # Get the request body
        body = json.loads(request.body)

        # If the post was not found
        if post is None:
            # Create a new one
            post = Post(id=post_id)

        # Validate the request body
        if not "author" in body or not "id" in body["author"]:
            return api_send_error("Missing author information.", 400)

        # Get the author
        author = Author.objects.get(id=body["author"]["id"])

        # Assign the post author
        post.author = author

        # Update the post data
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
            
        # Save the post
        post.save()

        # Send the post data
        return api_send_json(post.json())
    except Exception, e:
        return api_send_error(e.message, 500)

@csrf_exempt
def api_get_public_posts(request):
    '''
    This view handles api requests for public post data
    '''
    
    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # Get all public posts
        posts = [post.json() for post in Post.objects.select_related().filter(visibility='PUBLIC')]

        # Send the response
        return api_send_json(dict(posts=posts))
    except ObjectDoesNotExist, e:
        post = None
    except Exception, e:
        return api_send_error(e.message, 500)

@csrf_exempt
def api_get_posts_for_user(request):
    '''
    This view handles api requests to posts that should appear on a viewer's stream
    '''
    
    # Validate that it's a GET request
    if request.method != 'GET':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # Get the viewer
        viewer = api_get_viewer(request)

        # Get all the posts
        posts = Post.objects.order_by("-pubDate").select_related()
        
        # Only return posts that the user can view
        posts = [post.json() for post in posts if post.should_appear_on_stream_of(viewer)]

        # Send the response
        return api_send_json(dict(posts=posts))

    except ObjectDoesNotExist, e:
        return api_send_error("Author not found.", 404)
    except Exception, e:
        return api_send_error(e.message)

@csrf_exempt
def api_get_author_posts(request, user_id):
    '''
    This view handles api requests for an author's posts
    '''
    
    # Validate that it's a GET request
    if request.method != 'GET':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # Get the author whose posts are being requested
        author = Author.objects.get(pk=user_id)

        # Get the viewer
        viewer = api_get_viewer(request)

        # Only return posts that the user can 
        posts = [post.json() for post in author.get_posts_viewable_by(viewer)]

        # Send the response
        return api_send_json(dict(posts=posts))

    except Author.DoesNotExist, e:
        return api_send_error("Author not found.", 404)
    except Exception, e:
        return api_send_error(e.message)

@csrf_exempt
def api_send_friendrequest(request):
    '''
    This view handles api requests for an author's posts
    '''
    
    # Validate the request method
    if request.method != 'POST':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # Load request data
        frequest = json.loads(request.body)

        # Get the action
        action = frequest.get("query", "friendrequest")

        # Validate the action
        if not action in ("friendrequest", "unfriend"):
            return api_send_error("Wrong query parameter.", 400)

        # Validate request (friend)
        if not "friend" in frequest or not "author" in frequest["friend"] or not "id" in frequest["friend"]["author"]:
            return api_send_error("Missing friend data in request.", 400)

        # Validate request (author)
        if not "author" in frequest or not "id" in frequest["author"]:
            return api_send_error("Missing author data in request.", 400)

        # Get the friend and author data
        friend_data = frequest["friend"]["author"]
        author_data = frequest["author"]

        # Define function to get the corresponding Author instances
        def get_author(data):
            try:
                author = Author.objects.get(id=data["id"])

                return (True, author)
            except ObjectDoesNotExist, e:
                author = Author(id=data["id"], displayName=data["displayname"], host=remote_host)

                return (False, author)

        # Get the friend
        savedf, friend = get_author(friend_data)

        # Get the author
        saveda, author = get_author(author_data)

        # Check that one is local and one is remote
        if friend.is_local() == author.is_local():
            if friend.is_local():
                return api_send_error("The authors are local to this server and a remote server may not submit a friend request on their behalf.", 400)
            else:
                return api_send_error("None of the authors exist locally.", 404)

        # Save the author that needs to be saved
        if not savedf:
            friend.save()
        elif not saveda:
            author.save()

        # From now on, friend is the local user and author is the remote user
        if not friend.is_local():
            temp = friend
            friend = author
            author = temp

        try:
            # If the action is to send a friend request
            if action == "friendrequest":
                # Check if they are already friends
                if author.is_friends_with(friend):
                    # Just return success
                    return api_send_json(dict(error=False, message='Authors are already friends.'))

                # Check if the friend request already exists
                friendship = FriendRequest.objects.get(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author), accepted=False)

                # If it's just an attempt to resend a friend request
                if friendship.sender == author:
                    # Just return success
                    return api_send_json(dict(error=False, message='Friend request already sent.'))

                # Otherwise, it means that the author is trying to accept a previously sent friend request
                friendship.accepted = True
                friendship.save()

                # Return success
                return api_send_json(dict(error=False, message='Friend request sent.'))

            else:
                # Check if the friend request already exists
                friendship = FriendRequest.objects.get(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author))

                # If the friend request was not accepted
                if not friendship.accepted:
                    # If the sender was the remote author
                    if friendship.sender == author:
                        # Just remove the friend request
                        friendship.delete()
                    else:
                        # Otherwise, do nothing. Rejecting friend requests is not yet allowed.
                        pass
                else:
                    # Otherwise, we will leave the (ex) friend following the remote author

                    # If the sender was the remote author
                    if friendship.sender == author:
                        # Swap sender and receiver
                        friendship.sender = friend
                        friendship.receiver = author

                    # Change this to a follow relationship
                    friendship.accepted = False

                    # Save the friendship
                    friendship.save()

                # Return success
                return api_send_json(dict(error=False, message='Friendship removed.'))

        except FriendRequest.DoesNotExist, e:
            # If it's an unfriend request
            if action == "unfriend":
                return api_send_error("The friendship does not exist in the host.", 400)

            # Create friend request
            friendship = FriendRequest.objects.create(sender=author, receiver=friend, accepted=False)

            # Return success
            return api_send_json(dict(error=False, message='Friend request sent.'))

    except Exception, e:
        return api_send_error("Missing data in request.", 400)

@csrf_exempt
def api_search(request):
    '''
    This view handles api requests for searches
    '''
    
    # Validate the request method
    if request.method != 'GET':
        return api_send_error("Method not allowed.", 405)

    # Validate the request client
    valid = api_validate_client(request)

    # If the request client is invalid
    if not valid[0]:
        # Return the error
        return valid[1]
    else:
        # Otherwise, get the host making the request
        remote_host = valid[1]

    try:
        # If there's a query
        if "query" in request.GET:
            # Get the query term
            query = request.GET.get('query', None)

            # Retrieve the local authors
            local_authors = Author.objects.filter(Q(displayName__contains=query) | Q(user__username__contains=query), host__is_local=True)
        else:
            # Retrieve the local authors
            local_authors = Author.objects.filter(host__is_local=True)

        authors = []

        # Looping local authors to add the json version to the results
        for author in local_authors:
            authors.append(author.json())

        # Send the json version of the results
        return api_send_json(authors)

    except Exception, e:
        return api_send_error("Missing data in request.", 400)



# Site

def index(request):
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)
    if request.user.is_authenticated():
        return redirect(timeline)
    return render_to_response('main/index.html', {}, context)

def register(request):
    context = RequestContext(request)

    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        displayName = request.POST['displayName']
        github_name = request.POST['github_name']
        error = False

        if email is None or email == '':
            # Set error
            messages.error(request, 'Email is required.')
            error = True

        if username is None or username == '':
            # Set error
            messages.error(request, 'Username is required.')
            error = True

        if bool(re.compile(r'[^a-z0-9\-]').search(username)):
            # Set error
            messages.error(request, 'Username can only contain letters, numbers and hyphens.')
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
                # This should all be a transaction
                with transaction.atomic():
                    # Create and save the User wiith its username, email and password
                    user = User.objects.create_user(username, email, password)
                    
                    # Users start as inactive so the admin can activate them (except for tests)
                    if not settings.TESTING:
                        user.is_active = False
                        user.save()

                    # Create the Author and set the user and display name
                    author = Author(user=user, displayName=displayName, github_name=github_name)

                    # Assign the local host to the author
                    author.host = Host.get_local_host()

                    # Save the Author
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

@login_required
def timeline(request):
    context = RequestContext(request)
    user = request.user
    author = user.author
    posts = author.get_timeline_posts()

    # Render the timeline
    return render_to_response('main/timeline.html', {'posts': posts}, context)

def search(request):
    '''
    This view handles searches on the site
    '''
    context = RequestContext(request)
    user = request.user
    author = None

    if user.is_authenticated():
        author = user.author

    query = request.GET.get('query', None)
    posts = []
    local_authors = Author.objects.filter(displayName__contains=query, host__is_local=True).exclude(id=author.id if author is not None else None)
    friendships = []

    # Get the remote search results
    authors = RemoteApi.get_search_results(query)

    # Add the local authors to the result list
    authors.extend(local_authors)

    # Determine the friendships
    for matched_author in authors:
        # Determine if authors are friends
        are_friends = matched_author.is_friends_with(author)

        # If the authors are not friends
        if matched_author != author and author is not None and not are_friends:
            # Determine if the viewer has sent a friend request to the author
            sent_request = matched_author.friend_requests_received.filter(sender=author, accepted=False).count() > 0

            # Determine if the author has sent a friend request to the viewer
            try:
                received_request = author.friend_requests_received.get(sender=matched_author, accepted=False)
            except Exception, e:
                received_request = None
        else:
            sent_request = False
            received_request = None

        friendships.append((matched_author, are_friends, sent_request, received_request))

    return render_to_response('main/search.html', {'query': query, 'posts' : posts, 'friendships': friendships}, context)

def explore(request):
    '''
    This view renders all public posts, both local and remote
    '''
    context = RequestContext(request)

    # Get the local public posts
    posts = [post for post in Post.objects.select_related().filter(visibility='PUBLIC')]

    # Get the remote public posts
    posts.extend(RemoteApi.get_public_posts())

    # Sort the posts
    posts = sorted(posts, key=lambda p: p.pubDate if timezone.is_aware(p.pubDate) else pytz.UTC.localize(p.pubDate), reverse=True) 

    # Render the explore page
    return render_to_response('main/explore.html', {'posts' : posts}, context)


@login_required
def profile(request):
    '''
    This view displays the profile for the currently logged in user
    '''
    context = RequestContext(request)

    # Get the logged in user
    user = request.user

    # Redirect to the current logged in user's profile page
    return redirect('profile_author', username=user.username)

def profile_author_remote(request, host_id, author_id):
    '''
    This view displays the profile for a specific remote author
    '''
    context = RequestContext(request)

    try:
        # Get the host and author
        host, author = RemoteApi.get_author(host_id, author_id)

        # Validate the host and author
        if host is None or author is None:
            raise Http404

        # Create a user just to be able to display some fields
        user = User(username='N/A', email='N/A')
        author.user = user

        # The author that wants to see this profile
        viewer = request.user.author if request.user.is_authenticated() else None

        # Determine if the viewer and the profile owner are friends
        are_friends = False if viewer is None else viewer.is_friends_with(author)

        # If the authors are not friends
        if author != viewer and not are_friends:
            # Determine if the viewer has sent a friend request to the author
            sent_request = author.friend_requests_received.filter(sender=viewer, accepted=False).count() > 0

            # Determine if the author has sent a friend request to the viewer
            try:
                received_request = viewer.friend_requests_received.get(sender=author, accepted=False)
            except Exception, e:
                received_request = None
        else:
            sent_request = False
            received_request = None

        # Get all posts from this author viewable by the viewer
        posts = author.get_posts_viewable_by(viewer)

        # Sort the posts
        posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

        # Render the profile template
        return render_to_response('main/profile.html', {'posts' : posts, 'puser': user, 'friends': are_friends, 'sent_request': sent_request, 'received_request': received_request}, context)

    except Http404, e:
        raise
    except Exception, e:
        messages.error(request, "An error occured.")
        return redirect('index')

def profile_author(request, username):
    '''
    This view displays the profile for a specific user
    '''
    context = RequestContext(request)

    try:
        user = User.objects.get(username=username)

        # Author's profile
        author = user.author

        # The author that wants to see this profile
        viewer = request.user.author if request.user.is_authenticated() else None

        # Determine if the viewer and the profile owner are friends
        are_friends = False if viewer is None else viewer.is_friends_with(author)

        # If the authors are not friends
        if author != viewer and not are_friends:
            # Determine if the viewer has sent a friend request to the author
            sent_request = author.friend_requests_received.filter(sender=viewer, accepted=False).count() > 0

            # Determine if the author has sent a friend request to the viewer
            try:
                received_request = viewer.friend_requests_received.get(sender=author, accepted=False)
            except Exception, e:
                received_request = None
        else:
            sent_request = False
            received_request = None

        # Get all posts from this author viewable by the viewer
        posts = author.get_posts_viewable_by(viewer)

        # Render the profile
        return render_to_response('main/profile.html', {'posts' : posts, 'puser': user, 'friends': are_friends, 'sent_request': sent_request, 'received_request': received_request}, context)

    except ObjectDoesNotExist, e:
        raise Http404
    except Exception, e:
        messages.error(request, "An error occured.")
        return redirect('index')

@login_required
def profile_edit(request):
    '''
    This view is used to edit the profile for the currently logged in user
    '''
    context = RequestContext(request)
    
    if request.method == "POST":
        author = request.user.author
        displayName = request.POST.get('displayName')
        username = request.POST.get('username')
        email = request.POST.get('email')
        github_name = request.POST['github_name']

        if displayName is not None and displayName != '':
            author.displayName = displayName

        if username is not None and username != '':
            request.user.username = username

        if email is not None and email != '':
            request.user.email = email

        # Update: also set the github account:
        if github_name is not None:
            author.github_name = github_name

        try:
            # Save the User first
            request.user.save()
            # Save the Author last
            author.save()

            # Add a success flash message
            messages.info(request, "Your profile was updated successfully.")

            # Send the user to the profile screen
            return redirect('profile')
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

    return render_to_response('main/profileEdit.html', {}, context)

def post(request, post_id):
    '''
    This view is used to view a specific post
    '''
    context = RequestContext(request)
    user = request.user

    try:
        # Get the post
        post = Post.objects.get(pk=post_id)

        # Get the viewer
        viewer = user.author if user.is_authenticated() else None

        # If the post can't be viewed by the viwerd
        if not post.can_be_viewed_by(viewer):
            # Pretend it does not exist, don't send an unathorized message
            raise Http404
    except ObjectDoesNotExist, e:
        raise Http404

    return render_to_response('main/postView.html', {'post': post, 'full': True}, context)

@login_required
def post_new(request):
    '''
    This view is used to create a new post by the currently logged in user
    '''
    context = RequestContext(request)
    
    if request.method != "POST":
        raise Http404

    author = request.user.author
    title = request.POST.get('title')
    description = request.POST.get('description')
    body = request.POST.get('body')
    categories = request.POST.get('categories')
    visibility = request.POST.get('visibility')
    recipient = request.POST.get('recipient')
    contentType = request.POST.get('contentType')
    image = request.FILES.get('image')
    error = False

    # Escape html entities
    title = cgi.escape(title)
    description = cgi.escape(description)

    if title is None or title == '':
        # Set error
        messages.error(request, 'Title is required.')
        error = True

    if body is None or body == '':
        # Set error
        messages.error(request, 'Body is required.')
        error = True

    if visibility is None or visibility not in [x[0] for x in Post.VISIBILITY_OPTIONS]:
        # Set error
        messages.error(request, 'Visibility option is required.')
        error = True

    if contentType is None or contentType not in [x[0] for x in Post.CONTENTTYPE_OPTIONS]:
        # Set error
        messages.error(request, 'Content Type option is required.')
        error = True

    if recipient is not None and recipient != '':
        try:
            recipient = Author.objects.get(user__username=recipient)
        except ObjectDoesNotExist, e:
            # Set error
            messages.error(request, 'The recipient does not exist on our server.')
            error = True

    if error:
        if request.is_ajax():
            msgs = messages.get_messages(request)
            msgs = " ".join([str(msg) for msg in msgs])
            return api_send_error(msgs)

        # Send the user to the profile screen
        return redirect('profile')

    try:
        # Create the post
        post = Post()
        post.author = author
        post.title = title
        post.contentType = contentType
        post.description = description
        post.content = body
        post.pubDate = datetime.datetime.now()
        post.visibility = visibility
        post.recipient = recipient

        if post.contentType == 'text/html' and not validateHTML(body):
            error = "You can only use the following html tags: <a>, <b>, <blockquote>, <code>, <del>, <dd>, <dl>, <dt>, <em>, <h1>, <h2>, <h3>, <i>, <img>, <kbd>, <li>, <ol>, <p>, <pre>, <s>, <sup>, <sub>, <strong>, <strike>, <ul>, <br>, <hr>."
            
            if request.is_ajax():
                return api_send_error(error)

            # Set error
            messages.error(request, error)
            # Send the user to the profile screen
            return redirect('profile')

        # Save the Post
        post.save()

        if categories is not None and categories != '':
            categories = map(lambda x: x.strip(), categories.split(","))

            for category in categories:
                curcat = Category.objects.filter(name=category)
                
                if curcat and curcat.count() == 1:
                    post.categories.add(curcat[0])
                else:
                    curcat = Category(name=category)
                    curcat.save()
                    post.categories.add(curcat)

        if image is not None:
            post.image = image

        # Set the origin and the source
        post.origin = post.get_url()
        post.source = post.get_url()

        # Save the Post
        post.save()

        if request.is_ajax():
            return api_send_json(dict(post=render_to_string('main/post.html', {'post': post}, context)))

        # Add a success flash message
        messages.info(request, "Post created successfully.")

    except Exception, e:
        if request.is_ajax():
            return api_send_error(e.message)

        # Add the generic error
        messages.error(request, e.message)

    # Send the user to the profile screen
    return redirect('profile')

@login_required
def post_delete(request, post_id):
    '''
    This view is used to delete a specific post
    '''
    context = RequestContext(request)
    user = request.user
    author = user.author
    
    # Validate the request method
    if request.method != "POST":
        raise Http404

    try:
        # Get the post
        post = Post.objects.get(pk=post_id)
    except ObjectDoesNotExist,e:
        raise Http404

    # Validate that the author is trying to delete the post
    if post.author != author:
        messages.error(request, "You don't have permissions to delete this post.")
    else:
        # Otherwise, go ahead and delete the post
        post.delete()

        # Add a success flash message
        messages.info(request, "Post deleted successfully.")

    # Redirect to the post view
    return redirect('profile')

@login_required
def post_comment(request, post_id):
    '''
    This view is used to comment on a specific post
    '''
    context = RequestContext(request)
    user = request.user
    author = user.author
    body = request.POST.get('comment')

    try:
        # Get the post
        post = Post.objects.get(pk=post_id)
    except ObjectDoesNotExist,e:
        raise Http404

    if not post.can_be_viewed_by(author):
        raise Http404

    # Validate the comment
    if body is None:
        return redirect('post', post_id=post_id)
    
    # Create the comment
    comment = Comment.objects.create(post=post, author=author, comment=body)

    # Add a success flash message
    messages.info(request, "Comment added successfully.")

    # Redirect to the post view
    return redirect('post', post_id=post_id)

@login_required
def friends(request):
    context = RequestContext(request)
    author = request.user.author
    friends = author.friends()
    requests = author.requests()
    following = author.following()
    return render_to_response('main/friendView.html', {'friends': friends, 'requests': requests, 'following': following}, context)

@login_required
def request_friendship(request):
    context = RequestContext(request)
    author = request.user.author
    friend_id = request.POST.get('friend_id')
    host_id = request.POST.get('host_id')
    displayName = request.POST.get('displayName')
    
    # Validate the friend id
    if friend_id is None:
        messages.error(request, 'The user does not exist.')

    try:
        # If a host was specified
        if host_id is not None:
            # Get the host
            host = Host.objects.get(pk=host_id)
        else:
            # Otherwise, assume the host of the author (this host)
            host = author.host

        try:
            # Get the author to befriend
            friend = Author.objects.select_related('user').get(pk=friend_id)
        except ObjectDoesNotExist, e:
            # If the author to befriend was supposed to be local
            if host.is_local:
                # Raise the error if it does not exist
                raise

            # Otherwise, create the remote author
            friend = Author.objects.create(id=friend_id, host=host, displayName=displayName)

        # Check if the two authors are already friends
        if Author.are_friends(author.id, friend.id):
            # Set the error message
            messages.error(request, 'You are already friends with this user.')

        # Otherwise, check if there's a pending friend request
        elif FriendRequest.objects.filter(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author), accepted = False).count() > 0:
            # Set the error message
            messages.error(request, 'There\'s already a pending friend request between you and this user.')

        # Otherwise, send the friend request
        else:
            # If friend is remote
            if not friend.is_local():
                # First, try sending the friend request to remote host
                if not RemoteApi.send_friend_request(friend, author):
                    raise Exception('Could not send friend request to remote host.')

            # Create the friend request
            frequest = FriendRequest(sender=author, receiver=friend, accepted=False)

            # Save the friend request
            frequest.save()

            # Set the success message for the user
            messages.info(request, 'The friend request has been sent.')

        # If the friend is local
        if friend.is_local():
            # Redirect to the friend's profile view
            return redirect('profile_author', username=friend.user.username)
        else:
            # Otherwise, redirect to the friend's remote profile view
            return redirect('profile_author_remote', host_id=friend.host.id, author_id=friend.id)

    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The author to befriend does not exist.')

    except Exception, e:
        raise
        # Set the generic error message
        messages.error(request, 'The friend request could not be sent at the moment. Please try again later.')

    # Redirect to the friends view
    return redirect('friends')

@login_required
def remove_friendship(request):
    context = RequestContext(request)
    author = request.user.author
    friend_id = request.POST.get('friend_id')

    # Validate the friend id
    if friend_id is None:
        messages.error(request, 'The friendship does not exist.')

    try:
        # Get the friend
        friend = Author.objects.get(pk=friend_id)

        # Get the friendship
        friendship = FriendRequest.objects.get(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author))

        # If the friend is a remote author
        if not friend.is_local():
            # Try unfriending the friend in the remote host
            # Note that given that this was an optional feature, we're not making it a requirement
            # That is, if the remote host does not respond ok, we still proceed with unfriending locally

            RemoteApi.send_friend_request(friend, author, 'unfriend')

        # If the friend request was not accepted
        if not friendship.accepted:
            # If the sender was the local author
            if friendship.sender == author:
                # Just remove the friend request
                friendship.delete()
            else:
                # Otherwise, do nothing. Rejecting friend requests is not yet allowed.
                pass
        else:
            # Otherwise, we will leave the (ex) friend following the author

            # If the sender was the author
            if friendship.sender == author:
                # Swap sender and receiver
                friendship.sender = friend
                friendship.receiver = author

            # Change this to a follow relationship
            friendship.accepted = False

            # Save the friendship
            friendship.save()

        # Set the success message for the user
        messages.info(request, 'The friendship has been removed.')

        # If the friend is local
        if friend.is_local():
            # Redirect to the friend's profile view
            return redirect('profile_author', username=friend.user.username)
        else:
            # Otherwise, redirect to the friend's remote profile view
            return redirect('profile_author_remote', host_id=friend.host.id, author_id=friend.id)

    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The friendship does not exist.')

    except Exception, e:
        # Set the generic error message
        messages.error(request, 'The friendship could not be removed at the moment. Please try again later.')

    # Redirect to the friends view
    return redirect('friends')

@login_required
def accept_friendship(request):
    context = RequestContext(request)
    author = request.user.author
    request_id = request.POST.get('request_id')

    # Validate the request id
    if request_id is None:
        messages.error(request, 'The friend request does not exist.')

    try:
        # Get the friend request
        frequest = FriendRequest.objects.get(pk=request_id);

        # Validate that it's not accepted
        if frequest.accepted:
            messages.error(request, 'The friend request has already been accepted.')
        else:
            # Get the friend
            friend = frequest.sender

            # If friend is remote
            if not friend.is_local():
                # First, try sending the friend request to remote host
                if not RemoteApi.send_friend_request(friend, author):
                    raise Exception('Could not send the acceptance of the friend request to remote host.')

            # Accept the friend request
            frequest.accepted = True

            # Save the friend request
            frequest.save()

            # Set the success message for the user
            messages.info(request, 'The friend request has been accepted.')

            # If the friend is local
            if friend.is_local():
                # Redirect to the friend's profile view
                return redirect('profile_author', username=friend.user.username)
            else:
                # Otherwise, redirect to the friend's remote profile view
                return redirect('profile_author_remote', host_id=friend.host.id, author_id=friend.id)

    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The friend request does not exist.')
    except Exception, e:
        # Set the generic error message
        messages.error(request, 'The friend request could not be accepted at the moment. Please try again later.')

    # Redirect to the friends view
    return redirect('friends')


def validateHTML(body):
    parser = StackExchangeSite()
    parser.feed(body)#This is not the most efficient method, I couldn't find a way to stop the tag search once an invalid HTML tag is found. That is, the body is always iterated until the last bit of information. However, it is certainly safe.
    return parser.flag

class StackExchangeSite(HTMLParser):
    validTags = ["a", "b", "blockquote", "code", "del", "dd", "dl", "dt", "em", "h1", "h2", "h3", "i", "img", "kbd", "li", "ol", "p", "pre", "s", "sup", "sub", "strong", "strike", "ul", "br", "hr"]
    flag = True
    
    def handle_starttag(self, tag, attrs):
        if tag not in self.validTags:
	    self.flag = False

    def handle_endtag(self, tag):
        if tag not in self.validTags:
	    self.flag = False
    
    def handle_startendtag(self, tag, attrs):
	if tag not in self.validTags:
	    self.flag = False
