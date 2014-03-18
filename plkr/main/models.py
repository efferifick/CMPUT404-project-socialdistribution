from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
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


# Author Model
class Author(models.Model):
    id = UUIDField(primary_key=True, auto=True)
    user = models.OneToOneField(User)
    host = models.CharField(max_length = AUTHOR_HOST_MAX_SIZE)
    displayname = models.CharField(max_length = AUTHOR_DISPLAYNAME_MAX_SIZE)
    
    def get_url(self):
        return "%sauthor/%s" % (self.host, self.id)

    def is_friends_with(self, author):
        return Author.are_friends(self.id, author.id)

    @classmethod
    def are_friends(cls, author1_id, author2_id):
        if author1_id == author2_id:
            return True

        try:
            f = FriendRequest.objects.get(sender=author1_id, receiver = author2_id, accepted = True);
        except ObjectDoesNotExist,e:
            try:
                f = FriendRequest.objects.get(sender=author2_id, receiver = author1_id, accepted = True);
            except ObjectDoesNotExist,e:
                return False

        return True

    def list_of_follows(self):
        # TODO fix, should return Authors not friend requests
        return self.friend_requests_sent.get(accepted = False);

    def json(self):
        user = {} 
        user["id"] = self.id
        user["host"] = self.host
        user["displayname"] = self.displayname
        user["url"] = self.get_url()
        return user

    def __unicode__(self):
        return self.id

# Friend
class FriendRequest(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(Author, related_name ='friend_requests_sent')
    receiver = models.ForeignKey(Author, related_name ='friend_requests_received')
    accepted = models.BooleanField()
    
    def __unicode__(self):
        return str(self.id)

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

    # TODO Change this to a UUID auto field
    id = UUIDField(primary_key=True, auto=True)
    title = models.CharField(max_length= POST_TITLE_MAX_SIZE)
    author = models.ForeignKey(Author)
    source = models.URLField()
    origin = models.URLField()
    contentType = models.TextField(max_length = 13, choices = CONTENTTYPE_OPTIONS)
    description = models.CharField(max_length = POST_DESCRIPTION_MAX_SIZE)
    content = models.CharField(max_length = POST_CONTENT_MAX_SIZE)
    categories = models.ManyToManyField(Category)
    pubDate = models.DateField()
    visibility = models.TextField(max_length = 10, choices = VISIBILITY_OPTIONS)
    image = models.ImageField(upload_to='posts')

    def json(self):
        post = {} 
        post["title"] = self.title
        post["source"] = self.source
        post["origin"] = self.origin
        post["description"] = self.description
        post["content-type"] = self.contentType
        post["content"] = self.content
        post["author"] = Author.objects.get(id=self.author).json()
        post["categories"] = [c.name for c in self.categories.all()]
        post["comments"] = [com.json() for com in Comment.objects.filter(post=self.id)]
        post["pubDate"] = str(self.pubDate)
        post["guid"] = self.id
        post["visibility"] = self.visibility 

        return post

    def __unicode__(self):
        return unicode(self.id) or u''

    class Meta:
        ordering = ["-pubDate"]
        get_latest_by = "pubDate"

# Comment Model
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author)
    pubDate = models.DateField()
    comment = models.CharField(max_length = COMMENT_MAX_SIZE)
    post = models.ForeignKey(Post)

    def __unicode__(self):
        return self.id

    def json(self):
        comment = {}
        comment["author"] = self.author.json()
        comment["comment"] = self.comment
        comment["pubDate"] = str(self.pubDate)
        comment["guid"] = self.id
        return comment
