#!/usr/bin/env python
"""Builds the documentaion. First it runs gendoc to create rst files for the source code. Then it runs sphinx make.
.. Warning:: This will delete the content of the output directory first! So you might loose data.
             You can use updatedoc.py -nod.
Usage, just call::

  updatedoc.py -h

This is automatically executed when building with sphinx. Check the bottom of docs/conf.py.
"""
import os
import shutil

import gendoc


def prepare_dir(app, directory, delete=False):
    """Create apidoc dir, delete contents if delete is True.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :param directory: the apidoc directory. you can use relative paths here
    :type directory: str
    :param delete: if True, deletes the contents of apidoc. This acts like an override switch.
    :type delete: bool
    :returns: None
    :rtype: None
    :raises: None
    """
    app.info("Preparing output directories for jinjaapidoc.")
    if os.path.exists(directory):
        if delete:
            app.debug("Deleting dir %s", directory)
            shutil.rmtree(directory)
            app.debug("Creating dir %s", directory)
            os.mkdir(directory)
    else:
        app.debug("Creating %s", directory)
        os.mkdir(directory)


def main(app):
    """Parse the config of the app and initiate the generation process

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :returns: None
    :rtype: None
    :raises: None
    """
    c = app.config
    src = c.jinjaapi_srcdir

    if not src:
        return

    out = c.jinjaapi_outputdir or app.env.srcdir

    prepare_dir(app, out, not c.jinjaapi_nodelete)
    gendoc.generate(app, out, src,
                    exclude=c.jinjaapi_exclude_paths,
                    force=c.jinjaapi_force,
                    followlinks=c.jinjaapi_followlinks,
                    dryrun=c.jinjaapi_dryrun,
                    private=c.jinjaapi_includeprivate,
                    suffix=c.source_suffix,
                    template_dirs=c.jinjaapi_templatedirs)
