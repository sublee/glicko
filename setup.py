# -*- coding: utf-8 -*-
import re
from setuptools import setup
from setuptools.command.test import test


# use pytest instead
def run_tests(self):
    test_file = re.sub(r'\.pyc$', '.py', __import__(self.test_suite).__file__)
    raise SystemExit(__import__('pytest').main([test_file]))
test.run_tests = run_tests


setup(
    name='glicko',
    version='0.0.dev',
    license='BSD',
    author='Heungsub Lee',
    author_email='h' '@' 'subl.ee',
    url='http://github.com/sublee',
    description='An improvement of the Elo rating system',
    platforms='any',
    py_modules=['glicko', 'glicko2'],
    classifiers=['Development Status :: 1 - Planning',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.5',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Games/Entertainment'],
    install_requires=['distribute'],
    test_suite='glickotests',
    tests_require=['pytest'],
)
