The FieldDB Python client is functionality for connecting to
[FieldDB](https://github.com/OpenSourceFieldlinguistics/FieldDB) web services
from the command line or from the Python REPL or a Python program.

This module may be useful for developers or for people just wanting to interface
with the FieldDB web services. I am using it to understand how to use the
FieldDB and CouchDB APIs.


# Dependencies

* [FieldDB](https://github.com/OpenSourceFieldlinguistics/FieldDB) corpus and authentication services up and running
* Python [Requests](http://docs.python-requests.org/en/latest/) library


# Command-line usage

    $ ./fielddb-client.py -R http -H 127.0.0.1 -P 5984 -u username -p password


# In Python

    >>> c = fielddb_client.FieldDBClient('http', '127.0.0.1', '5984', 'username', 'password')
    >>> c.get_database_list()

