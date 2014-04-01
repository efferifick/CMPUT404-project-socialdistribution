# -v	Verbose.
# -H	Header. Example: -H "Content-Type: application/json"
# -X	Specifies a custom request method. Example: PUT

#!/bin/bash

F_REQUEST_FILE="f_request.json"
F_QUERY_FILE="f_query.json" 
AUTHOR_FILE="author.json" #TODO Can we update just from a json file?
POST_QUERY_FILE="post_query.json" 
POST_UPDATE_FILE="post_update.json"

USERID1="108ded43-8520-4035-a262-547454d32022"
USERID2="108ded43-8520-4035-a262-547454d32023"
POSTID="108ded43-8520-4035-a262-547454d32038"

FRIEND_REQUEST_URL="http://127.0.0.1:8000/friendrequest"
FRIEND_QUERY_URL="http://127.0.0.1:8000/friends/$USERID1"
F2F_QUERY_URL="http://127.0.0.1:8000/friends/$USERID1/$USERID2"
AUTHOR_URL="http://127.0.0.1:8000/author/$USERID1"
POST_UPDATE_URL="http://127.0.0.1:8000/post/$POSTID"
POST_QUERY_URL=$POST_UPDATE_URL

F_REQUEST_OUT_FILE="f_req_out.txt"
FRIEND_QUERY_OUT_FILE="f_query_out.txt"
F2F_QUERY_OUT_FILE="f2f_query_out.txt"
AUTHOR_OUT_FILE="author_out.txt"
AUTHOR_UPDATE_OUT_FILE="author_update_out_file.txt"
POST_QUERY_OUT_FILE="post_query_out.txt"
POST_QUERY_2_OUT_FILE="post_query_2_out.txt"
POST_UPDATE_OUT_FILE="post_update_out.txt"


#Friend request
curl \
	-s \
	-H "Content-Type: application/json" \
	-X POST \
	--data "@$F_REQUEST_FILE" \
	-o $F_REQUEST_OUT_FILE \
	$FRIEND_REQUEST_URL \
	2>&1

# Friend querying via POSTs to http://127.0.0.1:8000/friends/<userid>
curl \
	-s \
	-H "Content-Type: application/json" \
	-X POST \
	--data "@$F_QUERY_FILE" \
	-o $FRIEND_QUERY_OUT_FILE \
	$FRIEND_QUERY_URL \
	2>&1

# Friend 2 Friend querying via GETs to http://127.0.0.1:8000.friends/userid1/userid2
curl \
	-s \
	-H "Content-Type: application/json" \
	-X GET \
	-o $F2F_QUERY_OUT_FILE \
	$F2F_QUERY_URL \
	2>&1

# Get author profile
 curl \
	-s \
	-H "Content-Type: application/json" \
	-X GET \
	-o $AUTHOR_OUT_FILE \
	$AUTHOR_URL \
	2>&1

# Update author profile with put
curl \
	-s \
	-H "Content-Type: application/json"\
       	-X PUT \
	--data "@$AUTHOR_FILE" \
	-o $AUTHOR_UPDATE_OUT_FILE \
	$AUTHOR_URL \
	2>&1

# Get posts
curl \
	-s \
	-H "Content-Type: application/json"\
       	-X GET \
	-o $POST_OUT_FILE \
	$POST_QUERY_URL \
	2>&1

# Post (which should get) the post
curl \
	-s \
	-H "Content-Type: application/json"\
       	-X POST \
	--data "@$POST_QUERY_FILE" \
	-o $POST_2_OUT_FILE \
	$POST_QUERY_URL \
	2>&1

# Put (should insert or update) the post
curl \
	-s \
	-H "Content-Type: application/json" \
	-X PUT \
	--data "@$POST_UPDATE_FILE" \
	-o $POST_UPDATE_OUT_FILE \
	$POST_UPDATE_URL \
	2>&1
