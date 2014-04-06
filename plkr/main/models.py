from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django_extensions.db.fields import UUIDField

# Create your models here.

# Constants
STR_MAX_SIZE = 128 # Random number.

# Author constants
AUTHOR_ID_MAX_SIZE  = 40 # Based on json given to us.
AUTHOR_HOST_MAX_SIZE = STR_MAX_SIZE
AUTHOR_DISPLAYNAME_MAX_SIZE = STR_MAX_SIZE

# Post constants
POST_CONTENT_MAX_SIZE = 5000
POST_ID_MAX_SIZE = STR_MAX_SIZE 
POST_DESCRIPTION_MAX_SIZE = 140 # Basing on twitter's standards.
POST_TITLE_MAX_SIZE = STR_MAX_SIZE

# Comment constant
COMMENT_ID_MAX_SIZE = STR_MAX_SIZE
COMMENT_MAX_SIZE = 5000

# Friends list constants
FLIST_ID_MAX_SIZE = STR_MAX_SIZE

# Category constants
CAT_NAME_MAX_SIZE = STR_MAX_SIZE


# Host Model
class Host(models.Model):
    id = models.AutoField(primary_key=True)
    ip_address = models.GenericIPAddressField(unpack_ipv4=True,unique=True)
    port = models.PositiveIntegerField()
    prefix = models.CharField(max_length=20, default='/')
    is_local = models.BooleanField(default=False)

    @classmethod
    def get_local_host(cls):
        return Host.objects.get(pk=1, is_local=True)
    
    def get_url(self):
        # Gets the base url for the host
        return "http://%s:%d%s" % (self.ip_address, self.port, self.prefix)

    def __unicode__(self):
        return "%s:%d" % (self.ip_address, self.port)

# Author Model
class Author(models.Model):
    id = UUIDField(primary_key=True, auto=True)
    user = models.OneToOneField(User, null=True)
    host = models.ForeignKey(Host, related_name ='authors')
    displayName = models.CharField(max_length = AUTHOR_DISPLAYNAME_MAX_SIZE)
    github_name = models.CharField(max_length = AUTHOR_DISPLAYNAME_MAX_SIZE, blank=True)

    @classmethod
    def are_friends(cls, author1_id, author2_id):
        if author1_id == author2_id:
            return True

        try:
            FriendRequest.objects.get(Q(sender=author1_id, receiver = author2_id) | Q(sender=author2_id, receiver = author1_id), accepted = True);
        except ObjectDoesNotExist,e:
            return False

        return True

    def get_url(self):
        return "%sauthor/%s" % (self.host.get_url(), self.id)

    def is_friends_with(self, author):
        if author is None:
            return False

        return Author.are_friends(self.id, author.id)

    def friends(self):
        # Get all the authors that sent/received a friend request to/from this author, that was accepted already
        authors = Author.objects.filter(Q(friend_requests_sent__receiver=self.id, friend_requests_sent__accepted=True) | Q(friend_requests_received__sender=self.id, friend_requests_received__accepted=True))
        return authors

    def friendships(self):
        # Get all the friend requests that were sent/received by this author, that were accepted already
        requests = FriendRequest.objects.select_related('sender', 'receiver').filter(Q(receiver=self.id) | Q(sender=self.id), accepted=True)
        return requests

    def following(self):
        # Get all the authors that received a friend request from this author and has not accepted it yet
        authors = Author.objects.filter(friend_requests_received__sender=self.id, friend_requests_received__accepted=False)
        return authors

    def follows(self, author):
        # Determines if the author follows another author
        return self.following().filter(pk=author.id).count() > 0

    def requests(self):
        # Get all the friend requests sent to this author and that have not been accepted yet
        requests = FriendRequest.objects.select_related('sender').filter(receiver=self.id, accepted=False)
        return requests

    def is_foaf_of(self, author):
        # Determine if the author is a friend-of-a-friend of another author
        if author is None:
            return False

        # TODO implement
        return False

    def is_local(self):
        # Determines if the current author is local to this server
        return self.host.is_local

    def json(self):
        user = {} 
        user["id"] = self.id
        user["host"] = self.host.get_url()
        user["displayname"] = self.displayName
        user["url"] = self.get_url()
        return user

    def __unicode__(self):
        return self.displayName

# Friend
class FriendRequest(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(Author, related_name ='friend_requests_sent')
    receiver = models.ForeignKey(Author, related_name ='friend_requests_received')
    accepted = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s, %s: %d" % (self.sender.displayName, self.receiver.displayName, self.accepted)

# Category Model
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=CAT_NAME_MAX_SIZE, unique=True)

    def __unicode__(self):
        return unicode(self.name) or u''

    class Meta:
        verbose_name_plural = "categories"

# Post Model
class Post(models.Model):
    
    VISIBILITY_OPTIONS=(
        ("PUBLIC", "Public"),
        ("FOAF", "Friend of a Friend"),
        ("FRIENDS", "Friends"),
        ("PRIVATE", "Private"),
        ("SERVERONLY", "Server Only"),
    )

    CONTENTTYPE_OPTIONS=(
        ("text/plain", "Text"),
        ("text/html", "HTML"),
        ("text/markdown", "Markdown"),
    )

    id = UUIDField(primary_key=True, auto=True)
    title = models.CharField(max_length= POST_TITLE_MAX_SIZE)
    author = models.ForeignKey(Author, related_name='posts')
    source = models.URLField()
    origin = models.URLField()
    contentType = models.TextField(max_length = 13, choices = CONTENTTYPE_OPTIONS)
    description = models.CharField(max_length = POST_DESCRIPTION_MAX_SIZE)
    content = models.CharField(max_length = POST_CONTENT_MAX_SIZE)
    categories = models.ManyToManyField(Category)
    pubDate = models.DateTimeField(auto_now_add=True)
    visibility = models.TextField(max_length = 10, choices = VISIBILITY_OPTIONS)
    image = models.ImageField(upload_to='posts')

    def can_be_viewed_by(self, author):
        '''
        Determines if this post can be viewed by the specified author
        '''

        # If the post is public
        if self.visibility == 'PUBLIC':
            # It can be viewed
            return True

        # If the author is not logged in and the post is not public
        if author is None:
            # The post cannot be viewed
            return False

        # Check if it's the same user
        identity = self.author == author

        # Check if the viewer is in the same host as the post author
        in_server = identity or self.author.host == author.host

        # Only if it will be useful
        if self.visibility in ('FRIENDS', 'FOAF'):
            # Check if the viewer is friends with the post author
            are_friends = identity or Author.are_friends(self.author.id, author.id)
        else:
            are_friends = False

        # Initialize the check for foaf relationship
        are_friends_of_friends = are_friends

        # Only if it will be useful
        if self.visibility == 'FOAF' and not are_friends_of_friends:
            # Check if the viewer is a foaf of the post author
            are_friends_of_friends = author.is_foaf_of(self.author)

        # Return the appropriate value depending on the visibility of the post
        if self.visibility == 'PRIVATE':
            return identity
        elif self.visibility == 'SERVERONLY':
            return in_server
        elif self.visibility == 'FRIENDS':
            return are_friends
        elif self.visibility == 'FOAF':
            return are_friends_of_friends
        else:
            # Fallback should never get hit
            return False

    def should_appear_on_stream_of(self, author):
        '''
        Determines if this post should appear on the specified author's stream
        '''

        # If the author is None
        if author is None:
            # This post should not appear in a public stream
            return False

        # The author must be able to see the post
        can_view = self.can_be_viewed_by(author)

        # If the author and the post's author are friends, should be on stream
        are_friends = author.is_friends_with(self.author)

        # If the author is following the post's author, should be on stream
        is_following = are_friends or author.follows(self.author)

        # Return if the author is following the post's author and it can view the post
        return is_following and can_view

    def json(self):
        post = {} 
        post["title"] = self.title
        post["source"] = self.source
        post["origin"] = self.origin
        post["description"] = self.description
        post["content-type"] = self.contentType
        post["content"] = self.content
        post["author"] = self.author.json()
        post["categories"] = [c.name for c in self.categories.all()]
        post["comments"] = [com.json() for com in self.comments.all()]
        post["pubDate"] = format_date(self.pubDate)
        post["guid"] = self.id
        post["visibility"] = self.visibility 

        return post

    def __unicode__(self):
        return unicode(self.title) or u''

    class Meta:
        ordering = ["-pubDate"]
        get_latest_by = "pubDate"

# Comment Model
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author)
    pubDate = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length = COMMENT_MAX_SIZE)
    post = models.ForeignKey(Post, related_name='comments')

    def __unicode__(self):
        return "%s: %s..." % (self.author, self.comment[0:min(len(self.comment), 50)])

    def json(self):
        comment = {}
        comment["author"] = self.author.json()
        comment["comment"] = self.comment
        comment["pubDate"] = format_date(self.pubDate)
        comment["guid"] = self.id
        return comment


def format_date(date):
    '''
    Formats a given date in the format specified in the API requirements
    '''
    fDate = date.ctime()
    return fDate[:-4] + "UTC " + str(date.year)