# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__author__ = 'huang'


__all__ = ['DatabaseCreation']


from django.db.backends.postgresql_psycopg2.creation import DatabaseCreation as Psycopg2DatabaseCreation


class DatabaseCreation(Psycopg2DatabaseCreation):

    def _destroy_test_db(self, test_database_name, verbosity):
        # close non test db creation connection
        self.connection.pool.closeall()
        with self._nodb_connection.cursor() as cursor:
            cursor.execute("DROP DATABASE %s"
                           % self.connection.ops.quote_name(test_database_name))
