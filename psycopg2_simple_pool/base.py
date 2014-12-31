# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__author__ = 'huang'


from threading import Semaphore
from psycopg2 import pool
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as Psycopg2DatabaseWrapper


__all__ = ['DatabaseWrapper']


POOL_SETTING_KEY = 'DATABASE_POOL_ARGS'

DEFAULT_POOL_SETTING = {
    'MIN_CONN': 5,
    'MAX_CONN': 10
}

_pools = {}
_pools_lock = Semaphore(value=1)


def _create_pool(setting_key=POOL_SETTING_KEY, *args, **kwargs):
    pool_setting = DEFAULT_POOL_SETTING
    if hasattr(settings, setting_key):
        customized_setting = getattr(settings, setting_key)
        if isinstance(customized_setting, dict) and (
            'MIN_CONN' in customized_setting or
            'MAX_CONN' in customized_setting
        ):
            pool_setting.update(customized_setting)
        else:
            raise ImproperlyConfigured(
                'The setting requires a dict named `{0}` with values '
                'for keys named `MIN_CONN` and `MAX_CONN`!')

    return pool.ThreadedConnectionPool(pool_setting['MIN_CONN'],
                                       pool_setting['MAX_CONN'],
                                       *args,
                                       **kwargs)


class DatabaseWrapper(Psycopg2DatabaseWrapper):
    """ A database wrapper for pooling psycopg2 connections. """

    def __init__(self, *args, **kwargs):
        self._pool = None
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        from .creation import DatabaseCreation
        self.creation = DatabaseCreation(self)

    @property
    def pool(self):
        if self._pool is not None:
            return self._pool
        global _pools_lock
        global _pools
        _pools_lock.acquire()
        if not self.alias in _pools:
            self._pool = _create_pool(**self.get_connection_params())
            _pools[self.alias] = self._pool
        else:
            self._pool = _pools[self.alias]
        _pools_lock.release()
        return self._pool

    def close_all(self):
        with self.wrap_database_errors:
            global _pools
            for connection_pool in _pools.values():
                connection_pool.closeall()

    def get_new_connection(self, conn_params):
        if self.connection is None:
            self.connection = self.pool.getconn()
        return self.connection

    def _close(self):
        if self.connection.closed:
            self.pool.closeall()
        else:
            with self.wrap_database_errors:
                self._pool.putconn(self.connection)

    def set_clean(self):
        if self.in_atomic_block:
            self.closed_in_transaction = True
            self.needs_rollback = True
