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






if __name__ == '__main__':
    unittest.main()
