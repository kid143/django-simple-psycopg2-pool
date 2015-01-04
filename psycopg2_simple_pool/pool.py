# -*- coding: utf-8 -*-
from __future__ import unicode_literals


__author__ = 'huang'


__all__ = ['ThreadedConnectionPool', 'GeventConnectionPool']


from psycopg2.pool import (AbstractConnectionPool, ThreadedConnectionPool)


class GeventConnectionPool(AbstractConnectionPool):
    """ Gevent based coroutine supported Connection Pool. """

    def __init__(self, minconn, maxconn, *args, **kwargs):
        from gevent.lock import RLock
        super(GeventConnectionPool, self).__init__(minconn, maxconn, *args, **kwargs)
        self._lock = RLock()

    def getconn(self, key=None):
        """Get a free connection and assign it to 'key' if not None."""
        self._lock.acquire()
        try:
            return self._getconn(key)
        finally:
            self._lock.release()

    def putconn(self, conn=None, key=None, close=False):
        """Put away an unused connection."""
        self._lock.acquire()
        try:
            self._putconn(conn, key, close)
        finally:
            self._lock.release()

    def closeall(self):
        """Close all connections (even the one currently in use.)"""
        self._lock.acquire()
        try:
            self._closeall()
        finally:
            self._lock.release()
