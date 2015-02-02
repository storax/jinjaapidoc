"""
Tests for `jinjaapidoc` module.
"""
import os
import subprocess

here = os.path.abspath(os.path.dirname(__file__))


def test_buid():
    docdir = os.path.join(here, 'testdoc')
    out = os.path.join(docdir, 'build')
    src = os.path.join(docdir, 'source')

    errno = subprocess.call(['sphinx-build', src, out, '-W', '-v'])
    if errno != 0:
        raise SystemExit(errno)
