# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__author__ = 'huang'


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as Psycopg2DatabaseWrapper


__all__ = ['DatabaseWrapper']


POOL_SETTING_KEY = 'DATABASE_POOL_ARGS'

DEFAULT_POOL_SETTING = {
    'MIN_CONN': 5,
    'MAX_CONN': 10,
    'POOL_TYPE': 'threading',
    'ASYNC': False
}

_pools = {}
_pools_lock = None


def _create_pool(setting_key=POOL_SETTING_KEY, *args, **kwargs):
    pool_setting = DEFAULT_POOL_SETTING
    if hasattr(settings, setting_key):
        customized_setting = getattr(settings, setting_key)
        if not isinstance(customized_setting, dict) and not (
            'MIN_CONN' in customized_setting or
            'MAX_CONN' in customized_setting
        ):
            raise ImproperlyConfigured(
                'The setting requires a dict named `{0}` with values '
                'for keys named `MIN_CONN`, `MAX_CONN`, `ASYNC` AND `POOL_TYPE`!')

        if not 'POOL_TYPE' in customized_setting or not (
            customized_setting['POOL_TYPE'] in ('threading', 'gevent')
        ):
            raise ImproperlyConfigured(
                '`POOL_TYPE` currently only support `threading` and gevent!')
        pool_setting.update(customized_setting)

    if pool_setting['POOL_TYPE'] == 'threading':
        from .pool import ThreadedConnectionPool
        pool_class = ThreadedConnectionPool
    elif pool_setting['POOL_TYPE'] == 'gevent':
        from .pool import GeventConnectionPool
        pool_class = GeventConnectionPool
    else:
        raise ImproperlyConfigured(
            'The setting requires a valid asynchrounous type for asynchrounous'
            'database operation, currently only `threading` and `gevent` '
            'types are available')

    if 'ASYNC' in pool_setting and pool_setting['ASYNC']:
        if pool_setting['POOL_TYPE'] == 'threading':
            import select
            from psycopg2 import extensions

            # add callback

            def wait_select(conn):
                import psycopg2
                while 1:
                    state = conn.poll()
                    if state == extensions.POLL_OK:
                        break
                    elif state == extensions.POLL_READ:
                        select.select([conn.fileno()], [], [])
                    elif state == extensions.POLL_WRITE:
                        select.select([], [conn.fileno()], [])
                    else:
                        raise psycopg2.OperationalError("bad state from poll: %s" % state)

            extensions.set_wait_callback(wait_select)
        elif pool_setting['POOL_TYPE'] == 'gevent':
            import psycogreen.gevent
            psycogreen.gevent.patch_psycopg()

    return pool_class(pool_setting['MIN_CONN'],
                      pool_setting['MAX_CONN'],
                      *args,
                      **kwargs)


def ensure_lock(setting_key=POOL_SETTING_KEY):
    global _pools_lock
    if not _pools_lock:
        class DummyLock(object):
            def acquire(self):
                pass

            def release(self):
                pass

        if hasattr(settings, setting_key):
            customized_setting = getattr(settings, setting_key)
            if customized_setting['POOL_TYPE'] == 'threading':
                import threading
                _pools_lock = threading.Lock()
            elif customized_setting['POOL_TYPE'] == 'gevent':
                import gevent.lock
                _pools_lock = gevent.lock.RLock()
            else:
                raise ImproperlyConfigured(
                    'The setting requires a valid asynchrounous type for asynchrounous'
                    'database operation, currently only `threading` and `gevent` '
                    'types are available')
        else:
            _pools_lock = DummyLock()


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
        ensure_lock()
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
