from HTMLParser import HTMLParser
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import *
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
from main.models import *
import cgi, datetime, json, dateutil.parser, os.path, requests, urllib, hashlib

our_host = "http://127.0.0.1:8000/"

# API

def api_send_json(obj):
    '''
    This function returns the http response to send a serialized object to the client, in json format
    '''
    return HttpResponse(json.dumps(obj), content_type="application/json")

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
                # Otherwise, return the post data
                return api_send_json(post.json())
        
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
        # Check if viewer data was supplied
        if "id" in request.GET.keys():
            # Get the viewer id
            viewer_id = request.GET["id"]
            
            try:
                # Check if the viewer exists in our database
                viewer = Author.objects.get(pk=viewer_id)
            except ObjectDoesNotExist, e:
                # Assuming no viewer
                viewer = None
        else:
            # Assuming no viewer
            viewer = None

        # Get all the posts
        posts = Post.objects.order_by("-pubDate").select_related()
        
        # Only return posts that the user can 
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
        author = Author.objects.get(id=user_id)

        # Check if viewer data was supplied
        if "id" in request.GET.keys():
            # Get the viewer id
            viewer_id = request.GET["id"]

            try:
                # TODO (diego) I saw that the other team's used UUID's without the hyphens, maybe we would need to correct the format here

                # Check if the viewer exists in our database
                viewer = Author.objects.get(pk=viewer_id)
            except ObjectDoesNotExist, e:
                # Assuming no viewer
                viewer = None
        else:
            # Assuming no viewer
            viewer = None

        # Only return posts that the user can 
        posts = [post.json() for post in author.posts.all() if post.can_be_viewed_by(viewer)]

        # Send the response
        return api_send_json(dict(posts=posts))

    except ObjectDoesNotExist, e:
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

        # Validate request (friend)
        if not "friend" in frequest or not "author" in frequest["friend"] or not "id" in frequest["friend"]["author"]:
            return api_send_error("Missing friend data in request.", 400)

        # Validate request (author)
        if not "author" in frequest or not "id" in frequest["author"]:
            return api_send_error("Missing author data in request.", 400)

        # Get the friend and author data
        friend_data = frequest["friend"]["author"]
        author_data = frequest["author"]

        try:
            friend = Author.objects.get(id=friend_data["id"])

            # Validate that the friend is a local author
            if not friend.is_local():
                return api_send_error("Friend does not exist locally.", 404)
        except ObjectDoesNotExist, e:
            # Friend should be a local author
            return api_send_error("Friend does not exist locally.", 404)

        try:
            author = Author.objects.get(id=author_data["id"])

            # Validate that the author is NOT a local author
            if author.is_local():
                return api_send_error("The author is a local to this server and a remote server may not submit a friend request on its behalf.", 400)

            # Validate that the author host is the one making the request
            if author.host != remote_host:
                return api_send_error("The author is not local to the server making the request and thus the server should not submit a friend request on its behalf.", 400)

            # Check if they are already friends
            if author.is_friends_with(friend):
                return api_send_json(frequest)

            # Check if the friend request already exists
            friendship = FriendRequest.objects.get(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author), accepted=False);

            # If it's just an attempt to resend a friend request
            if friendship.sender == author:
                return api_send_json(frequest)

            # Otherwise, it means that the author accepted a previously sent friend request
            friendship.accepted = True
            friendship.save()

        except Author.DoesNotExist, e:
            # Validate more request data (author)
            if not "displayname" in author_data:
                return api_send_error("Missing author data in request.", 400)

            # Create the author
            author = Author.objects.create(id=author_data["id"], displayName=author_data["displayname"], host=remote_host)

            # Create friend request
            friendship = FriendRequest.objects.create(sender=author, receiver=friend, accepted=False);

        except FriendRequest.DoesNotExist, e:
            # Create friend request
            friendship = FriendRequest.objects.create(sender=author, receiver=friend, accepted=False);

        # Send the original request
        return api_send_json(frequest)

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
        # Get the query term
        query = request.GET.get('query', None)
        local_authors = Author.objects.filter(displayName__contains=query, host__is_local=True)
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
                # Update: also set the github account:

                author = Author(user=user, displayName=displayName, github_name = github_name)

                # Assign the local host to the author
                author.host = Host.get_local_host()

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

@login_required
def timeline(request):
    context = RequestContext(request)
    posts = timeline_posts(request)

    # Render the timeline
    return render_to_response('main/timeline.html', {'posts': posts}, context)

def timeline_posts(request):
    user = request.user
    author = user.author

    # TODO We have to build a function to get the user's stream
    # Maybe this isn't the best way to build the user's stream
    # but it filters out content we are not allowed to see.
    posts = Post.objects.order_by("-pubDate").select_related()
    
    # Filter the posts that can be viewed and that are supposed to be in the user's timeline
    posts = [post for post in posts if (post.can_be_viewed_by(author) and post.should_appear_on_stream_of(author))]

    # TODO This might need to change. This is showing github posts for friends/following in the author's timeline.
    # I (diego) think that the requirement is that my github activity is imported as my public activity.
    # Therefore, it should show up in my friends/followers timeline, as well as on my profile.
    # If that's true, we would just need to add this logic into profile (next function) as well.
    
    # Add github posts from all the author's friends
    for friend in author.friends():
        github_posts = get_authors_github_posts(friend)
        if github_posts:
            posts += github_posts

    # Add github posts from all the authors that the author follows
    for friend in author.following():
        github_posts = get_authors_github_posts(friend)
        if github_posts:
            posts += github_posts

    # Add the author's github posts
    github_posts = get_authors_github_posts(author)
    if github_posts:
        posts += github_posts

    # Sort the posts by publication date
    posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

    return posts


def search(request):
    '''
    This view handles searches on the site
    '''
    context = RequestContext(request)
    user = request.user
    author = None

    if user.is_authenticated:
        author = user.author

    query = request.GET.get('query', None)
    posts = []
    hosts = Host.objects.filter(is_local=False)
    local_authors = Author.objects.filter(displayName__contains=query, host__is_local=True)
    authors = []
    friendships = []

    # Query remote hosts
    # TODO Test this
    for host in hosts:
        try:
            # Get the user's github activity
            response = requests.get(host.get_search_url(), params=dict(query=query), timeout=0.3)

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
            print('Querying %s failed, query: "%s"' % (host.get_search_url(), query))

    # Add the local authors to the result list
    authors.extend(local_authors)

    # Determine the friendships
    for matched_author in authors:
        friendships.append((matched_author, matched_author.is_friends_with(author)))

    return render_to_response('main/search.html', {'query': query, 'posts' : posts, 'friendships': friendships}, context)


@login_required
def profile(request):
    '''
    This view displays the profile for the currently logged in user
    '''
    context = RequestContext(request)
    user = request.user
    author = user.author

    # Get the authors's posts ordered by date
    posts = author.posts.order_by("-pubDate").select_related()

    # We need to include the Github posts here
    # Here we retrieve the github posts from the current logged in user and display them on his profile.
    github_posts = get_authors_github_posts(author)
    if github_posts:
        posts = [post for post in posts]
        posts += github_posts
        posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

    return render_to_response('main/profile.html', {'posts' : posts, 'puser': user}, context)

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
        else:
            sent_request = False

        # Get all posts from this author
        posts = Post.objects.order_by("-pubDate").select_related().filter(author=author)

        # Filter the posts that can be viewed and that are supposed to be in the user's timeline
        posts = [post for post in posts if post.can_be_viewed_by(viewer)]

        # Here we retrieve the github posts from the user to 
        # display his github activity on his profile
        # So I, Paulo, agree with Diego that we should display it here
        github_posts = get_authors_github_posts(author)
        if github_posts:
            posts = [post for post in posts]

            posts += github_posts
            
            posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

        return render_to_response('main/profile.html', {'posts' : posts, 'puser': user, 'friends': are_friends, 'sent_request': sent_request}, context)
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
    post = Post.objects.get(pk=post_id)
    viewer = user.author if user.is_authenticated() else None

    if not post.can_be_viewed_by(viewer):
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

    if error:
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

        if post.contentType == 'text/html' and not validateHTML(body):
            # Set error
            messages.error(request, 'You can only use the following html tags: <a>, <b>, <blockquote>, <code>, <del>, <dd>, <dl>, <dt>, <em>, <h1>, <h2>, <h3>, <i>, <img>, <kbd>, <li>, <ol>, <p>, <pre>, <s>, <sup>, <sub>, <strong>, <strike>, <ul>, <br>, <hr>.')
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

        # Save the Post
        post.save()

        # Add a success flash message
        messages.info(request, "Post created successfully.")
    except Exception, e:
        # Add the generic error
        messages.error(request, e.message)

    # Send the user to the profile screen
    return redirect('profile')

@login_required
def post_delete(request, post_id):
    '''
    This view is used to delete a specific post
    '''
    # TODO
    pass

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
    friends = author.friends
    requests = author.requests
    return render_to_response('main/friendView.html', {'friends': friends, 'requests': requests}, context)

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
            # Create the friend request
            frequest = FriendRequest(sender=author, receiver=friend, accepted=False)

            # Save the friend request
            frequest.save()

            # If friend is remote
            if not friend.is_local():
                # TODO Send friend request to the remote server
                pass

            # Set the success message for the user
            messages.info(request, 'The friend request has been sent.')

        # If the friend is local
        if friend.is_local():
            # Redirect to the friend's profile view
            return redirect('profile_author', username=friend.user.username)
        else:
            # Otherwise, redirect to the list of friends
            return redirect('friends')

    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The author to befriend does not exist.')

    except Exception, e:
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
        # Get the friendship
        frequest = author.friendships().get(Q(receiver=friend_id) | Q(sender=friend_id))

        # Remove the friendship
        frequest.delete()

        # Set the success message for the user
        messages.info(request, 'The friendship has been removed.')
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
            # Accept the friend request
            frequest.accepted = True

            # Save the friend request
            frequest.save()

            # Set the success message for the user
            messages.info(request, 'The friend request has been accepted.')
    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The friend request does not exist.')
    except Exception, e:
        # Set the generic error message
        messages.error(request, 'The friend request could not be accepted at the moment. Please try again later.')

    # Redirect to the friends view
    return redirect('friends')


def get_authors_github_posts(author):
    '''
    This function returns a list of the author's github posts (if any)
    '''
    # Validate that the author has a github username specified
    if author.github_name is None or author.github_name == "":
        return None

    # Github user activity url
    url = "https://api.github.com/users/" + author.github_name + "/events/public"

    # Get the user's github activity
    response = requests.get(url, timeout=0.3);

    # Parse the response
    data = response.json()

    if ('message' in data and (data['message'] == 'Not Found' or 'API rate limit exceeded' in data['message'] )):
        return None

    resp = []

    # Loop on all the activity
    for p in data:
        # Create a post for each activity
        gpost = GitHubPost()
        gpost.source = "http://github.com/" + author.github_name
        gpost.gitHub = True
        gpost.title = "GitHub " + p["type"]
        gpost.author = author
        gpost.contentType = "text/plain"
        gpost.pubDate = dateutil.parser.parse(p["created_at"])
        gpost.visibility = "PUBLIC"

        if p["type"] == "PushEvent":
            gpost.source = p["payload"]["commits"][0]["url"]
            gpost.source = gpost.source.replace('api.github.com','github.com')
            gpost.source = gpost.source.replace('/repos/','/')
            gpost.source = gpost.source.replace('/commits/','/commit/')

            gpost.origin = p["payload"]["commits"][0]["url"]
            gpost.description = p["payload"]["commits"][0]["message"]

        elif p["type"] == "ForkEvent":
            gpost.source = p["payload"]["forkee"]["html_url"]
            gpost.origin = p["repo"]["url"]
            gpost.description = "Fork " + p["payload"]["forkee"]["name"] + " from " + p["repo"]["name"]

        elif p["type"] == "CommitCommentEvent":
            gpost.source = p["payload"]["comment"]["html_url"]
            gpost.origin = p["payload"]["comment"]["url"]
            gpost.description = p["payload"]["comment"]["body"]

        # Add the post to the resulting list
        resp.append(gpost)

    return resp


class GitHubPost(Post):
    '''
    Post subclass for GitHub posts
    '''

    def __init___(self):
        self.origin = "https://github.com/"

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
