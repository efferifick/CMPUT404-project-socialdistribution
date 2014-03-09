from django.db import models
from django.contrib.auth.models import User

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
POST_CONTENTTYPE_MAX_SIZE = STR_MAX_SIZE

# Comment constant
COMMENT_ID_MAX_SIZE = STR_MAX_SIZE
COMMENT_MAX_SIZE = 5000

# Friends list constants
FLIST_ID_MAX_SIZE = STR_MAX_SIZE

# Category constants
CAT_NAME_MAX_SIZE = STR_MAX_SIZE


# Author Model
class Author(models.Model):
    # max_length is based on the json given to us.
    id = models.CharField(max_length = AUTHOR_ID_MAX_SIZE , primary_key=True, unique=True)
    user = models.OneToOneField(User)
    host = models.CharField(max_length = AUTHOR_HOST_MAX_SIZE)
    displayname = models.CharField(max_length = AUTHOR_DISPLAYNAME_MAX_SIZE)
    url = models.URLField()
    
    def json(self):
        user = {} 
        user["id"] = self.id
        user["host"] = self.host
        user["displayname"] = self.displayname
        user["url"] = self.url
        return user

    def __unicode__(self):
        return self.id


class FriendRequest(models.Model):
    id = models.AutoField(primary_key=True)
    user_who_sent_request = models.ForeignKey(Author, related_name ='user_who_sent_requested')
    user_who_received_request = models.ForeignKey(Author, related_name ='user_who_received_requested')
    accepted = models.BooleanField()
    
    def __unicode__(self):
        return str(self.id)

'''
class SubscriptionList(models.Model):
    
    user_url = models.URLField(primary_key=True, unique=True)

    def __unicode__(self):
        return self.id
'''

# Category Model
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=CAT_NAME_MAX_SIZE, unique=True)

    def __unicode__(self):
        return self.name

# Post Model
class Post(models.Model):
    
    VISIBILITY_OPTIONS=(
        ("PUBLIC", "Public"),
        ("FOAF","Friend of a Friend"),
        ("FRIENDS","Friends"),
        ("PRIVATE","Private"),
        ("SERVERONLY","Server Only"),
    )

    id = models.CharField(max_length=POST_ID_MAX_SIZE, primary_key=True, unique=True)
    title = models.CharField(max_length= POST_TITLE_MAX_SIZE)
    author = models.ForeignKey(Author)
    source = models.URLField()
    origin = models.URLField()
    contentType = models.CharField(max_length = POST_CONTENTTYPE_MAX_SIZE)
    description = models.CharField(max_length = POST_DESCRIPTION_MAX_SIZE)
    content = models.CharField(max_length = POST_CONTENT_MAX_SIZE)
    categories = models.ManyToManyField(Category)
    pubDate = models.DateField()
    visibility = models.TextField(max_length = 10, choices = VISIBILITY_OPTIONS)

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
        return self.id

# Comment Model
class Comment(models.Model):
    id = models.CharField(max_length=COMMENT_ID_MAX_SIZE, primary_key=True, unique=True)
    author = models.ForeignKey(Author)
    pubdate = models.DateField()
    comment = models.CharField(max_length = COMMENT_MAX_SIZE)
    post = models.ForeignKey(Post)

    def __unicode__(self):
        return self.id

    def json(self):
        comment = {}
        comment["author"] = self.author.json()
        comment["comment"] = self.comment
        comment["pubDate"] = str(self.pubdate)
        comment["guid"] = self.id
        return comment