### Gravatar code
#
# This code was provided by gravatar at https://en.gravatar.com/site/implement/images/django/
#
# This is reponsible for getting the url from the user's email addres on gravatar.com and geting 
# his avatar image url, and then this url will be used on the profile.html page.

### gravatar.py ###############
### place inside a 'templatetags' directory inside the top level of a Django app (not project, must be inside an app)
### at the top of your page template include this:
### {% load gravatar %}
### and to use the url do this:
### <img src="{% gravatar_url 'someone@somewhere.com' %}">
### or
### <img src="{% gravatar_url sometemplatevariable %}">
### just make sure to update the "default" image path below
from django import template
import urllib, hashlib

register = template.Library()

class GravatarUrlNode(template.Node):
    def __init__(self, email):
        self.email = template.Variable(email)
 
    def render(self, context):
        try:
            email = self.email.resolve(context)
        except template.VariableDoesNotExist:
            return ''
 
        default = "http:///static/images/defaultavatar.jpg"
        size = 40
 
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
 
        return gravatar_url
 
@register.tag
def gravatar_url(parser, token):
    try:
        tag_name, email = token.split_contents()
 
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
 
    return GravatarUrlNode(email)    