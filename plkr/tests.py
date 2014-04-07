import unittest
import json
import requests

EXISTING_USER = 'dluces'
BASEHOST = 'http://127.0.0.1'
BASEPORT = '8000'
HEADERS = {"accept": "application/json"}
TIMEOUT = 1.5

class TestSequence(unittest.TestCase):


    def setUp(self):
        self.baseurl = BASEHOST + ':' + BASEPORT
        self.test_existing_user_search()

    def test_existing_user_search(self):
        author = EXISTING_USER
        url = self.baseurl + '/api/search?query=' + author
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        different_key = False
        try:
            for author in data:
                for key in author.keys():
                    if (key not in ("url", "host", "displayname", "id")):
                        different_key = True
                        break
                    if key == "displayname" and author[key] == "dluces":
                        self.dluces = author
        except:
            self.assertTrue(False, "something went wrong")

        self.assertFalse(different_key, "We are sending a different key")
        self.assertTrue(self.dluces["url"] == "http://10.4.10.5:8080/author/108ded43-8520-4035-a262-547454d32022", "URLs is different")
        self.assertTrue(self.dluces["host"] == "http://10.4.10.5:8080/", "Host is different")
        self.assertTrue(self.dluces["displayname"] == "dluces", "displayname is different")
        self.assertTrue(self.dluces["id"] == "108ded43-8520-4035-a262-547454d32022", "id is different")

    def test_nonexisting_user_search(self):
        author = "hello+world"
        url = self.baseurl + '/api/search?query=' + author
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        self.assertTrue(not data, "data was not empty")

    def test_get_author_profile(self):
        url = self.baseurl + '/author/' + self.dluces["id"]
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        self.assertTrue(self.dluces == data, "existing user is not the same as what the author profile says")

    def test_is_author_friends_with_non_existing_user_using_http_get(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"]) + '/THISISNOTAUSER'
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertTrue(data["query"] == "friends", "we are sending an invalid query field")
        self.assertTrue(data["friends"] == "NO", "user is friend with invalid user")

    def test_is_author_friends_with_existing_nonfriend_user_using_http_get(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"]) + '/108ded43-8520-4035-a262-547454d32024'
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertTrue(data["query"] == "friends", "we are sending an invalid query field")
        self.assertTrue(data["friends"] == "NO", "user is friend with non friend user")

    def test_is_author_friends_with_existing_friend_using_http_get(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"]) + '/108ded43-8520-4035-a262-547454d32023'
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertTrue(data["query"] == "friends", "we are sending an invalid query field")
        self.assertTrue(data["friends"] == "YES", "user is not friend with friend user")

    def test_is_author_friends_with_these_people_that_are_not_users(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"])
        payload = {"query": "friends", "author": str(self.dluces["id"])}
        fake_authors = ["hello", "this", "are", "all", "not", "real", "authors", "12938", "<>", "!@#"]

        payload["authors"] = fake_authors
        response = requests.post(url, headers=HEADERS, timeout=TIMEOUT, data=json.dumps(payload))
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "author", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertFalse(data["friends"], "there is a friend in what should be an empty friend's list")

    def test_is_author_friends_with_this_people_who_he_is_not_friends_with(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"])
        payload = {"query":"friends", "author": str(self.dluces["id"])}
        real_non_friend_author = "108ded43-8520-4035-a262-547454d32024"
        payload["authors"] = real_non_friend_author
        response = requests.post(url, headers=HEADERS, timeout=TIMEOUT, data=json.dumps(payload))
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "author", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertFalse(data["friends"], "author should not be friends with user")

    def test_is_author_friends_with_friend(self):
        url = self.baseurl + '/friends/' + str(self.dluces["id"])
        payload = {"query":"friends", "author": str(self.dluces["id"])}
        real_friend = "108ded43-8520-4035-a262-547454d32023"
        payload["authors"] = real_friend
        response = requests.post(url, headers=HEADERS, timeout=TIMEOUT, data=json.dumps(payload))
        data = response.json()
        different_keys = False
        for key in data:
            if key not in ("query", "author", "friends"):
                different_keys = True
        self.assertFalse(different_keys, "we are sending an invalid key")
        self.assertTrue("108ded43-8520-4035-a262-547454d32023" not in data["friends"], "author should be friends with user")

    def test_making_users(self):

        url = self.baseurl + '/register'

        response = requests.get(url, timeout=TIMEOUT)

        csrf = response.cookies['csrftoken']



        payload = {u"email":u"eochoa@ualberta.ca",
                u"username":u"efferifick",
                u"password":u"password",
                u"displayName":u"displayName",
                u"github_name":u"efferifick",
                u"csrfmiddlewaretoken": unicode(csrf)
                }

        response = requests.post(url, timeout=TIMEOUT, data=payload)


        # Now we should test whether or not we can find this author...

        url = self.baseurl + '/api/search?query=' + payload["displayName"]
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = response.json()

        different_key = False
        try:
            for author in data:
                for key in author.keys():
                    if (key not in ("url", "host", "displayname", "id")):
                        different_key = True
                        break
                    if key == "displayname" and author[key] == "displayName":
                        self.author = author
        except:
            self.assertTrue(False, "something went wrong")

        if self.author != None:
            print self.author

if __name__ == '__main__':
    unittest.main()
