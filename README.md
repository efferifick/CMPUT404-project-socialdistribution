CMPUT404-project-socialdistribution
===================================

Welcome to our term project for CMPUT404-project-socialdistribution.

See project.org (plain-text/org-mode) for a description of the project as well as required functionality. 

* Demo video at: https://www.youtube.com/watch?v=SjshqZlXHBw&edit=vd


Contributors / Licensing
========================

Project authors:
	- Diego Luces
	- Paulo Henrique Moreno
	- Marcus Vinicius Alves da Silva
	- Erick Ochoa
	- Brandon Hayduk

Generally everything is LICENSE'D under the Apache 2 license by Abram Hindle.

All text is licensed under the CC-BY-SA 4.0 http://creativecommons.org/licenses/by-sa/4.0/deed.en_US

Contributors:

    - Olexiy Berjanskii
    - Erin Torbiak
    - Abram Hindle


Setup / Installation
========================
Dateutil:
This is required to parse dates from imported GitHub posts

	pip install python-dateutil

Django:
This application uses Django

	pip install django

Django Dajaxice:
This is required for using ajax

	pip install django-dajaxice

Django Extensions DB:
This is required for the UUIDField class

	pip install django-extensions

Django IPware:
This is required for retrieving the client's IP address

	pip install django-ipware

Markdown2:
This is required to parse posts in markdown format

	pip install django-markdown-deux

Pillow:
This is required to handle image fields in models

Note that Pillow also needs python-dev package (Ubuntu) to be installed.

	pip install pillow

Pytz:
This is required to do date operations that are timezone-aware

	pip install pytz

Requests:
This is required to send requests to other server

	pip install requests

Simple Gravatar:

	pip install django-simple-gravatar

