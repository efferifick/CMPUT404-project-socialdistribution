from django.db import models

# Create your models here.

Class User(models.Model):



Class Post(models.Model):
    '''
    id = models.CharField(max_length=128, primary_key=True, unique=True)
    title = models.CharField(max_length=128)
    source = model.URLField()
    contentType = model.CharField(max_length = 20)
    origin = model.URLField()
    description = model.CharField(max_length = 140)
    content = model.CharField(max_length = 1200)
    categories = 
    '''

Class Comment(model.Model):



Class FriendsList(model.Model):
    '''
    id = models.CharField(max_length=128, primary_key=True, unique=True)
    user_who_sent_request = models.ForeignKey(User, unique=True) 
    user_who_received_request = models.ForeignKey(User, unique=True) 
    accepted = models.BooleanField()
    '''

