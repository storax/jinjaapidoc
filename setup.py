#!/usr/bin/env python

from __future__ import print_function
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand
import io
import os
import sys


here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


long_description = read('README.rst', 'HISTORY.rst')
install_requires = ['jinja2', 'sphinx']
tests_require = ['pytest']


setup(
    name='jinjaapidoc',
    version='0.3.1',
    description='Sphinx API Doc with Jinja2 templates',
    long_description=long_description,
    author='David Zuber',
    author_email='zuber.david@gmx.de',
    url='https://github.com/storax/jinjaapidoc',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'jinjaapidoc': ['templates/*.rst',
                                  'autosummarytemplates/*.rst']},
    include_package_data=True,
    tests_require=tests_require,
    install_requires=install_requires,
    cmdclass={'test': PyTest},
    entry_points={
        'console_scripts': [
            'jinjaapidoc = jinjaapidoc.updatedoc:main',
        ],
    },
    license='BSD',
    zip_safe=False,
    keywords='jinjaapidoc',
    test_suite='jinjaapidoc.test.jinjaapidoc',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Documentation :: Sphinx',
        'Framework :: Sphinx :: Extension',
    ],
)
