# django-simple-psycopg2-pool

This is a [psycopg2](https://github.com/psycopg/psycopg2) based pool for Django's  ORM.
The code is tested under Django 1.7 but should work with
Django 1.6.

This pool uses psycopg2's native ThreadPool for pooling.

## Usage

First set the database engine to `psycopg2_simple_pool`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'psycopg2_simple_pool', 
        'USER': '<user>', 
        'PASSWORD': '<password>', 
        'HOST': 'localhost', 
        'PORT': 5432
    }
}
```

The pooling args can be configured in Django project's `setting.py`:

```python
DATABASE_POOL_ARGS = {
    'MIN_CONN': 5,
    'MAX_CONN': 10,
    'POOL_TYPE': 'threading', 
    'ASYNC': True
}
```

Currently pool type only support `threading` and `gevent`, 
the latter option requires gevent library.

The `ASYNC` parameter will use asynchronous I/O for connections. 


## License

The project is distributed with MIT license.
