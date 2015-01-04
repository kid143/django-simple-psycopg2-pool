# -*- coding: utf-8 -*-

from distutils.core import setup

required = [
    'psycopg2',
    'Django'
]

setup(
    name='django-simple-psycopg2-pool',
    version='1.2.0',
    packages=['psycopg2_simple_pool'],
    url='https://github.com/kid143/django-simple-psycopg2-pool',
    license='MIT',
    author='kid143',
    author_email='h@anrenmind.com',
    description='A simple psycopg2 connection pool for Django',
    long_description= open('README.md', 'r').read(),
    classifiers=(
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 2.5',
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3.0',
        # 'Programming Language :: Python :: 3.1',
    ),
)
