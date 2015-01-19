#!/usr/bin/env python
"""Builds the documentaion. First it runs gendoc to create rst files for the source code. Then it runs sphinx make.
.. Warning:: This will delete the content of the output directory first! So you might loose data.
             You can use updatedoc.py -nod.
Usage, just call::

  updatedoc.py -h

This is automatically executed when building with sphinx. Check the bottom of docs/conf.py.
"""
import argparse
import os
import logging
import shutil
import sys

import gendoc


log = logging.getLogger(__name__)
thisdir = os.path.abspath(os.path.dirname(__file__))


def setup_argparse():
    """Sets up the argument parser and returns it

    :returns: the parser
    :rtype: :class:`argparse.ArgumentParser`
    :raises: None
    """
    log.debug("Setting up argparser.")
    parser = argparse.ArgumentParser(
        description="Builds the documentaion. First it runs gendoc to create rst files\
        for the source code. Then it runs sphinx make.\
        WARNING: this will delete the contents of the output dirs. You can use -nod.")
    parser.add_argument('src', help='Path to the source directory')
    parser.add_argument('out', action='store', dest='destdir',
                        help='Directory to place all output')
    parser.add_argument('exclude_paths', help='Paths to exclude', nargs='*')
    parser.add_argument('-f', '--force', action='store_true', dest='force',
                        help='Overwrite existing files')
    parser.add_argument('-l', '--follow-links', action='store_true',
                        dest='followlinks', default=False,
                        help='Follow symbolic links. Powerful when combined '
                        'with collective.recipe.omelette.')
    parser.add_argument('-n', '--dry-run', action='store_true', dest='dryrun',
                        help='Run the script without creating files')
    parser.add_argument('-P', '--private', action='store_true',
                        dest='includeprivate',
                        help='Include "_private" modules')
    parser.add_argument('-s', '--suffix', action='store', dest='suffix',
                        help='file suffix (default: rst)', default='rst')
    parser.add_argument('-nod', '--nodelete', action='store_true',
                        help='Do not empty the output directories first.')
    return parser


def prepare_dir(directory, delete=True):
    """Create apidoc dir, delete contents if delete is True.

    :param directory: the apidoc directory. you can use relative paths here
    :type directory: str
    :param delete: if True, deletes the contents of apidoc. This acts like an override switch.
    :type delete: bool
    :returns: None
    :rtype: None
    :raises: None
    """
    if os.path.exists(directory):
        if delete:
            assert directory != thisdir, 'Trying to delete docs! Specify other output dir!'
            log.debug("Deleting %s", directory)
            shutil.rmtree(directory)
            log.debug("Creating %s", directory)
            os.mkdir(directory)
    else:
        log.debug("Creating %s", directory)
        os.mkdir(directory)


def main(argv=None):
    """Parse commandline arguments and run the tool

    :param argv: the commandline arguments.
    :type argv: list
    :returns: None
    :rtype: None
    :raises: None
    """
    if argv is None:
        argv = sys.argv[1:]
    parser = setup_argparse()
    args = parser.parse_args(argv)
    log.debug("Preparing output directories")
    prepare_dir(args.destdir, not args.nodelete)
    gendoc.generate(args.src, args.destdir,
                    exclude=args.exclude_paths,
                    force=args.force,
                    followlinks = args.followlinks,
                    dry=args.dryrun,
                    private=args.includeprivate,
                    suffix=args.suffix)

if __name__ == '__main__':
    main()
