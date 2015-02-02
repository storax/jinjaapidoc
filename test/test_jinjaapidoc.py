"""
Tests for `jinjaapidoc` module.
"""
import os
import shutil
import subprocess

import pytest

here = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope='function')
def fix_doc(request):
    """Create the _static dir. For finalizer delete the output dir and build dir"""
    docdir = os.path.join(here, 'testdoc')
    staticdir = os.path.join(docdir, 'source', '_static')
    if not os.path.exists(staticdir):
        os.mkdir(staticdir)

    def fin():
        shutil.rmtree(os.path.join(docdir, 'build'))
        shutil.rmtree(os.path.join(docdir, 'source', 'jinjaapiout'))

    request.addfinalizer(fin)


def test_buid(fix_doc):
    docdir = os.path.join(here, 'testdoc')
    out = os.path.join(docdir, 'build')
    src = os.path.join(docdir, 'source')

    subprocess.check_call(['sphinx-build', src, out, '-W', '-v', '-N'])
