#!/usr/bin/python
# coding=utf8

# Copyright 2013 Joel Dunham
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""FieldDB Client --- functionality for connecting to FieldDB web services.

This module may be useful for developers or for people just wanting to get their
FieldDB data into Python. It's also good for understanding how to use the FieldDB
and CouchDB APIs.

"""

import requests
import pprint
import simplejson
import uuid
import copy
import optparse

# For logging HTTP requests & responses
import logging
try:
    import http.client as http_client
except ImportError:
    import httplib as http_client # Python 2


def verbose():
    """Call this to spit the HTTP requests/responses to stdout.
    From http://stackoverflow.com/questions/10588644/how-can-i-see-the-entire-http-request-thats-being-sent-by-my-python-application
    I don't know how it works or how to turn it off once it's called ...

    """

    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


class FieldDBClient(object):
    """Create a FieldDB instance to connect to live FieldDB web services.

    Basically this is just some FieldDB-specific conveniences wrapped around
    a Python `requests.Session` instance.

    """

    def __init__(self, protocol='https', host='localhost', port='3183',
        username='', password=''):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({'Content-Type': 'application/json'})

    # General Methods
    ############################################################################

    def get_url(self):
        return '%s://%s:%s' % (self.protocol, self.host, self.port)

    def get_url_auth(self):
        return '%s://%s:%s@%s:%s' % (self.protocol, self.username,
            self.password, self.host, self.port)

    def get_uuid(self):
        return uuid.uuid4().hex

    # General Couch Requests
    ############################################################################

    def get_greeting(self):
        print
        print self.get_url()
        print
        r = self.session.get(self.get_url())
        try:
            return r.json()
        except:
            return r.text

    # Databases
    ############################################################################

    def get_database_list(self):
        url = '%s/_all_dbs' % self.get_url()
        return self.session.get(url).json()

    def create_database(self, database_name):
        url = '%s/%s' % (self.get_url_auth(), database_name)
        return self.session.put(url).json()

    def delete_database(self, database_name):
        url = '%s/%s' % (self.get_url_auth(), database_name)
        return self.session.delete(url).json()

    def replicate_database(self, source_name, target_name):
        url = '%s/_replicate' % self.get_url_auth()
        payload=simplejson.dumps({
            'source': source_name,
            'target': target_name,
            'create_target': True})
        return self.session.post(
            url,
            data=payload,
            headers={'content-type': 'application/json'}).json()

    # Documents
    ############################################################################

    def create_document(self, database_name, document):
        document = simplejson.dumps(document)
        url = '%s/%s' % (self.get_url_auth(), database_name)
        return self.session.post(
            url,
            data=document,
            headers = {'content-type': 'application/json'}).json()

    def get_document(self, database_name, document_id):
        url = '%s/%s/%s' % (self.get_url_auth(), database_name, document_id)
        return self.session.get(url).json()

    def get_all_docs_list(self, database_name):
        url = '%s/%s/_all_docs' % (self.get_url(), database_name)
        return self.session.get(url, params={'include_docs': 'true'}).json()

    def update_document(self, database_name, document_id, document_rev,
        new_document):
        url = '%s/%s/%s' % (self.get_url_auth(), database_name, document_id)
        new_document['_rev'] = document_rev
        return self.session.put(url,
            data=simplejson.dumps(new_document),
            headers = {'content-type': 'application/json'}).json()


class FieldDBClientTester(object):
    """Class with a `test` method that has a bunch of `assert` statements that
    make sure that a FieldDBClient instance is behaving as we expect it to. Most
    of this is straight out of http://guide.couchdb.org/

    Usage::

        >>> tester = FieldDBClientTester(fielddb_client)
        >>> tester.test()

    """

    def __init__(self, fielddb_instance, database_name='fruits',
        database_clone_name='fruits_clone'):
        self.fielddb = fielddb_instance
        self.database_name = database_name
        self.database_clone_name = database_clone_name

    fruits = {
        "orange": {
            "item" : "orange",
            "prices" : {
                "Fresh Mart" : 1.99,
                "Price Max" : 3.19,
                "Citrus Circus" : 1.09
            }
        },
        "apple": {
            "item" : "apple",
            "prices" : {
                "Fresh Mart" : 1.59,
                "Price Max" : 5.99,
                "Apples Express" : 0.79
            }
        },
        "banana": {
            "item" : "banana",
            "prices" : {
                "Fresh Mart" : 1.99,
                "Price Max" : 0.79,
                "Banana Montana" : 4.22
            }
        }
    }

    def clean_up_couch(self):
        """Clean up the couch by deleting the databases we've created.

        """

        database_list = self.fielddb.get_database_list()
        if self.database_name in database_list:
            self.fielddb.delete_database(self.database_name)
        if self.database_clone_name in database_list:
            self.fielddb.delete_database(self.database_clone_name)

    def test(self):
        """Run some tests be manipulating the couch and verifying that it
        behaves as expected.  Just simple `assert` statements.

        """

        print '\nTesting the FieldDB client.'

        self.clean_up_couch() # Clean Up.

        # Get the CouchDB greeting.
        greeting = self.fielddb.get_greeting()
        assert greeting.has_key('couchdb')
        print '... Got CouchDB greeting.'

        # Get the database list.
        database_list = self.fielddb.get_database_list()
        assert type(database_list) is type([])
        print '... Got database list.'

        # Create a database.
        if self.database_name not in database_list:
            create_response = self.fielddb.create_database(self.database_name)
            assert create_response['ok'] is True
            print '... Created database "%s".' % self.database_name
        else:
            print '... Database "%s" already exists.' % self.database_name

        # Create documents.
        apple_create_response = self.fielddb.create_document(self.database_name,
            self.fruits['apple'])
        orange_create_response = self.fielddb.create_document(self.database_name,
            self.fruits['orange'])
        banana_create_response = self.fielddb.create_document(self.database_name,
            self.fruits['banana'])
        apple_id = apple_create_response['id']
        orange_id = apple_create_response['id']
        banana_id = apple_create_response['id']
        assert apple_create_response['ok'] is True
        assert orange_create_response['ok'] is True
        assert banana_create_response['ok'] is True
        assert type(apple_id) is unicode # id is a UUID, e.g., u'59da119f7911695425ab79f8a7060709'}
        assert len(apple_id) is 32
        print '... Created apple, orange, and banana documents.'

        # Get a document.
        banana = self.fielddb.get_document(self.database_name, banana_id)
        assert banana.has_key('_id')
        assert banana['_id'] == banana_id
        assert banana.has_key('_rev')
        assert banana['_rev'][0] == u'1'
        assert banana.has_key('item')
        assert type(banana['prices']) is dict
        print '... Retrieved the banana document.'

        # Update a document.
        new_banana = copy.deepcopy(self.fruits['banana'])
        new_banana['foo'] = 'bar'
        new_banana['item'] = 'waaaaanana'
        update_response = self.fielddb.update_document(self.database_name,
            banana['_id'], banana['_rev'], new_banana)
        assert update_response['rev'][0] == u'2'
        assert update_response['ok'] is True
        assert update_response['id'] == banana_id
        print '... Updated the banana document.'

        # Get an updated document.
        new_banana = self.fielddb.get_document(self.database_name, banana['_id'])
        assert new_banana['_id'] == banana_id
        assert new_banana['item'] == u'waaaaanana'
        print '... Retrieved the updated banana.'

        # Replicate a database.
        replicate_response = self.fielddb.replicate_database(self.database_name,
            self.database_clone_name)
        new_database_list = self.fielddb.get_database_list()
        assert len(new_database_list) == len(database_list) + 2
        print '... Replicated database "%s".' % self.database_name

        # Get all documents in a database
        all_docs_list = self.fielddb.get_all_docs_list(self.database_name)
        assert len(all_docs_list) == 3
        print '... Got the three fruit documents in the database.'

        # Design Documents
        ########################################################################

        data = {
            "_id": "_design/example",
            "views": {
                "foo": {
                    "map": "function(doc){emit(doc._id, doc._rev)}"
                },
                "add_syntactic_category": {
                    "map": open('map1.js', 'r').read()
                }
            }
        }
        dd_create_response = self.fielddb.create_document(self.database_name, data)
        assert dd_create_response['id'] == u'_design/example'
        assert dd_create_response['rev'][0] == u'1'
        print '... Created a design document.'

        """

        print '\n' * 7
        view = self.fielddb.get_document(self.database_name, '_design/example/_view/foo')
        pprint.pprint(view)

        print '\n' * 7
        view = self.fielddb.get_document('jrwdunham-firstcorpus', '_design/example/_view/add_syntactic_category')
        pprint.pprint(view)

        """

        # Clean Up.
        self.clean_up_couch()
        print


if __name__ == '__main__':

    """Use this module as a command-line utility.
    Basic usage::

        $ ./fielddb-client.py -R http -H 127.0.0.1 -P 5984 -u admin -p none

    """

    parser = optparse.OptionParser()

    parser.add_option("-R", "--protocol", default="https",
        help="protocol: one of 'https' or 'http' [default: %default]")
    parser.add_option("-H", "--host", default="localhost",
        help="hostname where the FieldDB application can be accessed [default: %default]")
    parser.add_option("-P", "--port", default="3183",
        help="port of the FieldDB application being used for the research [default: %default]")
    parser.add_option("-u", "--username", default="username",
        help="username of the FieldDB researcher (on the FieldDB application) [default: %default]")
    parser.add_option("-p", "--password", default="password",
        help="password of the FieldDB researcher (on the FieldDB application) [default: %default]")

    (options, args) = parser.parse_args()

    # Currently the utility just creates a FieldDB client based on the input
    # parameters and then runs the simple "test suite" (`test` method) of the
    # `FieldDBClientTester`.

    fielddb_client = FieldDBClient(
        options.protocol,
        options.host,
        options.port,
        options.username,
        options.password
    )

    tester = FieldDBClientTester(fielddb_client)
    tester.test()

