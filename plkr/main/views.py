import datetime
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
import json, urllib, dateutil.parser
from main.models import *
import os.path

our_host = "http://127.0.0.1:8000/"

# API

def api_send_json(obj):
    '''
    This function returns the http response to send a serialized object to the client, in json format
    '''
    return HttpResponse(json.dumps(obj), content_type="application/json")

def api_send_error(message):
    '''
    This function returns the http response for errors (sending status 400 as it's always the user's fault)
    '''
    return HttpResponse(json.dumps(dict(error=True, message=message)), content_type="application/json", status=400)

def api_get_author(request, user_id):
    # Get the author information
    context = RequestContext(request)
    author = Author.objects.get(id=user_id)
    return api_send_json(author.json())

def api_author_has_friends(request, user1_id):
    context = RequestContext(request)

    if request.method != 'POST':
        raise Http404

    resp = dict()
    
    resp["query"] = "friends"
    resp["author"] = user1_id
    
    try:
        flist = json.loads(request.body)
        flist = flist["authors"]
        friends = [f for f in flist if Author.are_friends(user1_id, f)]
        resp["friends"] = friends

        return api_send_json(resp)
    except Exception, e:
        return api_send_error(e.message)

def api_authors_are_friends(request, user1_id, user2_id):
    context = RequestContext(request)

    if request.method != 'GET':
        raise Http404

    resp = dict()
    resp["query"] = "friends"

    try:
        if Author.are_friends(user1_id, user2_id):
            resp["friends"] = "YES"
        else:
            resp["friends"] = "NO"

        return api_send_json(resp)
    except Exception, e:
        return api_send_error(e.message)


def api_get_post(request, post_id):
    context = RequestContext(request)
    
    try:
        post = Post.objects.get(id=post_id)
    except Exception, e:
        post = {}

    if request.method == 'POST' or request.method == 'GET':
        return api_send_json(post.json())
    
    elif request.method == 'PUT':
        body = json.loads(request.body)

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

        return api_send_json(post.json())
    else:
        raise Http404

def api_get_author_posts(request, user_id):
    # Get the all posts by the user
    #
    context = RequestContext(request)
    
    return None 

def api_send_friendrequest(request):
    context = RequestContext(request)

    if request.method != 'POST':
        raise Http404

    try:
        frequest = json.loads(request.body)

        friend_data = frequest["friend"]["author"]
        author_data = frequest["author"]

        friend = Author.objects.get(id=friend_data["id"])

        flist = FriendRequest(sender=author["id"], receiver=friend["id"], accepted=False)
        flist.save()

        return HttpResponse(json.dumps(frequest), content_type="application/json")
    except Exception, e:
        return api_send_error(e.message)


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
                author = Author(user=user, displayName=displayName)
                author.host = 'http://localhost:8000/'

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


    # TODO We have to build a function to get the user's stream
    # Maybe this isn't the best way to build the user's stream
    # but it filters out content we are not allowed to see.



    posts = Post.objects.order_by("-pubDate").select_related()
    user = request.user
    author = user.author

    """
    for post in posts:
    
        #Check if I can view this post
        #Check if I should view the post
        if not post.can_be_viewed_by(author) or not post.should_appear_on_stream_of(author):
            print("aaa")
            posts = posts.exclude(id=post.id)
    """

    posts = [post for post in posts if (post.can_be_viewed_by(author) or post.should_appear_on_stream_of(author))]

    # TODO
    # Add github posts ( from all my friends and followers )
    for aut in author.friends():
        github_posts = get_authors_github_posts(aut)
        if github_posts:
            posts += github_posts

    for aut in author.following():
        github_posts = get_authors_github_posts(aut)
        if github_posts:
            posts += github_posts

    github_posts = get_authors_github_posts(author)
    if github_posts:
        posts += github_posts

    posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

    return render_to_response('main/timeline.html', {'posts': posts}, context)

@login_required
def profile(request):
    '''
    This view displays the profile for the currently logged in user
    '''
    context = RequestContext(request)
    user = request.user
    author = user.author
    posts = author.posts.order_by('-pubDate').select_related()

    #We need to include the Github posts here
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
        author = user.author
        posts = author.posts.order_by('-pubDate').select_related()

        #Include the users github posts
        github_posts = get_authors_github_posts(author)
        if github_posts:
            posts = [post for post in posts]

            posts += github_posts
            
            posts = sorted(posts, key=lambda p: p.pubDate, reverse=True) 

        return render_to_response('main/profile.html', {'posts' : posts, 'puser': user}, context)
    except Exception, e:
        raise Http404

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

        if displayName is not None and displayName != '':
            author.displayName = displayName

        if username is not None and username != '':
            request.user.username = username

        if email is not None and email != '':
            request.user.email = email

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
    #TODO: Body should be escaped if it is plain text
    #TODO: We should only allow a subset of html.
    categories = request.POST.get('categories')
    visibility = request.POST.get('visibility')
    contentType = request.POST.get('contentType')
    image = request.FILES.get('image')
    error = False

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

    if not error:
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

            # Save the Post
            post.save()

            if categories is not None and categories != '':
                categories = map(lambda x: x.strip(), categories.split(","))

                if len(categories) > 0:
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
    
    # Validate the friend id
    if friend_id is None:
        messages.error(request, 'The user does not exist.')

    try:
        # Get the author to befriend
        friend = Author.objects.select_related('user').get(pk=friend_id)

        # Get the username of the author to befriend
        username = friend.user.username

        # Check if there's already a friend request between the two authors
        if Author.are_friends(author.id, friend.id):
            # Set the error message
            messages.error(request, 'You are already friends with this user.')
            # Redirect to the friend's profile view
            return redirect('profile_author', username=username)

        # Check if there's a pending friend request
        count = FriendRequest.objects.filter(Q(sender=author, receiver=friend) | Q(sender=friend, receiver=author), accepted = False).count()
        if count > 0:
            # Set the error message
            messages.error(request, 'There\'s already a pending friend request between you and this user.')
            # Redirect to the friend's profile view
            return redirect('profile_author', username=username)            

        # Create the friend request
        frequest = FriendRequest(sender=author, receiver=friend, accepted=False)

        # Save the friend request
        frequest.save()

        # Set the success message for the user
        messages.info(request, 'The friend request has been sent.')
    except ObjectDoesNotExist,e:
        # Set the error message
        messages.error(request, 'The author to befriend does not exist.')
        # Redirect to the friends view
        return redirect('friends')
    except Exception, e:
        # Set the generic error message
        messages.error(request, 'The friend request could not be sent at the moment. Please try again later.')

    # Redirect to the friends view
    return redirect('profile_author', username=username)

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
    resp = []

    if author.github_enabled:
        url = "https://api.github.com/users/" + author.github_name + "/events/public"
        response = urllib.urlopen(url);
        data = json.loads(response.read())
        if not ('message' in data and data['message'] == 'Not Found'):
            for p in data:
                gpost = GitHubPost()
                gpost.title = "GitHub " + p["type"]
                gpost.author = author
                gpost.contentType = "text/plain"
                gpost.pubDate = dateutil.parser.parse(p["created_at"])
                gpost.visibility = "PUBLIC"

                if p["type"] == "PushEvent":
                    gpost.source = p["payload"]["commits"][0]["url"]
                    gpost.origin = p["payload"]["commits"][0]["url"]
                    gpost.content = p["payload"]["commits"][0]["message"]

                elif p["type"] == "ForkEvent":
                    gpost.source = p["payload"]["forkee"]["git_url"]
                    gpost.origin = p["repo"]["url"]
                    gpost.content = "Fork " + p["payload"]["forkee"]["name"] + " from " + p["repo"]["name"]

                resp.append(gpost)

    return resp


class GitHubPost(Post):
    def __init___(self):
        gpost.source = "https://github.com/"
        gpost.origin = "https://github.com/"