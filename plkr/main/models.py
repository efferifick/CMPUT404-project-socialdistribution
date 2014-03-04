from django.db import models

# Create your models here.

# Constants
STR_MAX_SIZE = 128 # Random number.

# User constants
USER_ID_MAX_SIZE = 40 # Based on json given to us.
USER_HOST_MAX_SIZE = STR_MAX_SIZE
USER_DISPLAYNAME_MAX_SIZE = STR_MAX_SIZE

# Post constants
POST_CONTENT_MAX_SIZE = 5000
POST_ID_MAX_SIZE = STR_MAX_SIZE 
POST_DESCRIPTION_MAX_SIZE = 140 # Basing on twitter's standards.
POST_TITLE_MAX_SIZE = STR_MAX_SIZE
POST_CONTENTTYPE_MAX_SIZE = STR_MAX_SIZE

# Comment constant
COMMENT_ID_MAX_SIZE = MAX_STR
COMMENT_MAX_SIZE = 5000

# Friends list constants
FLIST_ID_MAX_SIZE = MAX_STR

# Category constants
CAT_NAME_MAX_SIZE = MAX_STR


Class User(models.Model):
    '''
    # max_length is based on the json given to us.
    id = models.CharField(max_length = USER_ID_MAX_SIZE, primary_key=True, unique=True)
    host = models.CharField(max_length = USER_HOST_MAX_SIZE)
    displayname = models.CharField(max_length = USER_DISPLAYNAME_MAX_SIZE)
    url = models.URLField()

    def __unicode__(self):
        return self.id
    '''

Class Category(models.Model):
    '''
    name = models.CharField(max_length=CAT_NAME_MAX_SIZE, unique=True)

    def __unicode__(self):
        return self.name
    '''

Class Post(models.Model):
    '''
    id = models.CharField(max_length=POST_ID_MAX_SIZE, primary_key=True, unique=True)
    title = models.CharField(max_length= POST_TITLE_MAX_SIZE)
    author = models.ForeignKey(User)
    source = model.URLField()
    origin = model.URLField()
    contentType = model.CharField(max_length = POST_CONTENTTPE_MAX_SIZE)
    description = model.CharField(max_length = POST_DESCRIPTION_MAX_SIZE)
    content = model.CharField(max_length = POST_CONTENT_MAX_SIZE)
    categories = models.ManyToMany(Category)

    def __unicode__(self):
        return self.id
    '''

Class Comment(model.Model):
    '''
    id = models.CharField(max_length=COMMENT_ID_MAX_SIZE, primary_key=True, unique=True)
    author = models.ForeignKey(User)
    pubdate = models.DateField()
    comment = models.CharField(max_length = COMMENT_MAX_SIZE)
    post = models.ForeignKey(Post)

    def __unicode__(self):
        return self.id
    '''


Class FriendsList(model.Model):
    '''
    id = models.CharField(max_length=FLIST_ID_MAX_SIZE, primary_key=True, unique=True)
    user_who_sent_request = models.ForeignKey(User, unique=True)
    user_who_received_request = models.ForeignKey(User, unique=True)
    accepted = models.BooleanField()
    
    def __unicode__(self):
        return self.id
    '''

