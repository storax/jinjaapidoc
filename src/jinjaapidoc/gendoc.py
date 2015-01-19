#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    this is a modification of sphinx.apidoc by David.Zuber
    It uses jinja templates to render the rst files.

    sphinx.apidoc
    ~~~~~~~~~~~~~

    Parses a directory tree looking for Python modules and packages and creates
    ReST files appropriately to create code documentation with Sphinx.

    This is derived from the "sphinx-autopackage" script, which is:
    Copyright 2008 Societe des arts technologiques (SAT),
    http://www.sat.qc.ca/

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import sys
import optparse
import inspect
import pkgutil
import logging
from os import path

import jinja2
from sphinx.util.osutil import walk
from sphinx.ext import autosummary

log = logging.getLogger(__name__)

INITPY = '__init__.py'
PY_SUFFIXES = set(['.py', '.pyx'])
TEMPLATE_DIRS = ['_templates']


def make_loader(template_dirs=None):
    """Return a new :class:`jinja2.FileSystemLoader` that uses the template_dirs

    :param template_dirs: searchpath for templates.
    :type template_dirs: list | None
    :returns: a new loader
    :rtype: :class:`jinja2.FileSystemLoader`
    :raises: None
    """
    if template_dirs is None:
        template_dirs = TEMPLATE_DIRS
    log.debug('Creating loader with template dirs: %s', template_dirs)
    return jinja2.FileSystemLoader(searchpath=template_dirs)


def make_environment(loader, options=None):
    """Return a new :class:`jinja2.Environment` with the given loader

    :param loader: a jinja2 loader
    :type loader: :class:`jinja2.BaseLoader`
    :param options: environment options
    :type options: :class:`dict`
    :returns: a new environment
    :rtype: :class:`jinja2.Environment`
    :raises: None
    """
    if options is None:
        options = {}
    if loader:
       options['loader'] = loader
    log.debug('Creating environment with options: %s', options)
    return jinja2.Environment(**options)


def makename(package, module):
    """Join package and module with a dot."""
    # Both package and module can be None/empty.
    if package:
        name = package
        if module:
            name += '.' + module
    else:
        name = module
    return name


def write_file(name, text, opts):
    """Write the output file for module/package <name>."""
    fname = path.join(opts.destdir, '%s.%s' % (name, opts.suffix))
    if opts.dryrun:
        log.info('Would create file %s.', fname)
        return
    if not opts.force and path.isfile(fname):
        log.info('File %s already exists, skipping.', fname)
    else:
        log.info('Creating file %s.' % fname)
        f = open(fname, 'w')
        try:
            f.write(text)
        finally:
            f.close()


def import_name(name):
    """Import the given name and return name, obj, parent, mod_name

    :param name: name to import
    :type name: str
    :returns: the imported object or None
    :rtype: object | None
    :raises: None
    """
    try:
        log.debug('Importing %r', name)
        name, obj = autosummary.import_by_name(name)[:2]
        log.debug('Imported %s', obj)
        return obj
    except ImportError as e:
        log.exception("Failed to import %r: %s", name, e)


def get_members(mod, typ, include_public=None):
    """Return the memebrs of mod of the given type

    :param mod: the module with members
    :type mod: module
    :param typ: the typ, ``'class'``, ``'function'``, ``'exception'``, ``'data'``, ``'members'``
    :type typ: str
    :param include_public: list of private members to include to plublics
    :type include_public: list | None
    :returns: None
    :rtype: None
    :raises: None
    """
    include_public = include_public or []
    tests = {'class': lambda x: inspect.isclass(x) and not issubclass(x, BaseException),
             'function': lambda x: inspect.isfunction(x),
             'exception': lambda x: inspect.isclass(x) and issubclass(x, BaseException),
             'data': lambda x: not inspect.ismodule(x) and not inspect.isclass(x) and not inspect.isfunction(x),
             'members': lambda x: True}
    items = []
    for name in dir(mod):
        i = getattr(mod, name)
        inspect.ismodule(i)

        if tests.get(typ, lambda x: False)(i):
            items.append(name)
    public = [x for x in items
              if x in include_public or not x.startswith('_')]
    log.debug('Got members of %s of type %s: public %s and %s', mod, typ, public, items)
    return public, items


def _get_submodules(module):
    """Get all submodules for the given module/package

    :param module: the module to query or module path
    :type module: module | str
    :returns: list of module names and boolean whether its a package
    :rtype: list
    :raises: TypeError
    """
    if inspect.ismodule(module):
        if hasattr(module, '__path__'):
            p = module.__path__
        else:
            return []
    elif isinstance(module, basestring):
        p = module
    else:
        raise TypeError("Only Module or String accepted. %s given." % type(module))
    log.debug('Getting submodules of %s', p)
    l = [(name, ispkg) for loader, name, ispkg in pkgutil.iter_modules(p)]
    log.debug('Found submodules of %s: %s', module, l)
    return l


def get_submodules(module):
    """Get all submodules without packages for the given module/package

    :param module: the module to query or module path
    :type module: module | str
    :returns: list of module names excluding packages
    :rtype: list
    :raises: TypeError
    """
    l = _get_submodules(module)
    return [name for name, ispkg in l if not ispkg]


def get_subpackages(module):
    """Get all subpackages for the given module/package

    :param module: the module to query or module path
    :type module: module | str
    :returns: list of packages names
    :rtype: list
    :raises: TypeError
    """
    l = _get_submodules(module)
    return [name for name, ispkg in l if ispkg]


def get_context(package, module, fullname):
    """Return a dict for template rendering

    Variables:

      * :package: The top package
      * :module: the module
      * :fullname: package.module
      * :subpkgs: packages beneath module
      * :submods: modules beneath module
      * :classes: public classes in module
      * :allclasses: public and private classes in module
      * :exceptions: public exceptions in module
      * :allexceptions: public and private exceptions in module
      * :functions: public functions in module
      * :allfunctions: public and private functions in module
      * :data: public data in module
      * :alldata: public and private data in module
      * :members: dir(module)


    :param package: the parent package name
    :type package: str
    :param module: the module name
    :type module: str
    :param fullname: package.module
    :type fullname: str
    :returns: a dict with variables for template rendering
    :rtype: :class:`dict`
    :raises: None
    """
    var = {'package': package,
           'module': module,
           'fullname': fullname}
    log.debug('Creating context for: package %s, module %s, fullname %s', package, module, fullname)
    obj = import_name(fullname)
    if not obj:
        for k in ('subpkgs', 'submods', 'classes', 'allclasses',
                  'exceptions', 'allexceptions', 'functions', 'allfunctions',
                  'data', 'alldata', 'memebers'):
            var[k] = []
        return var

    var['subpkgs'] = get_subpackages(obj)
    var['submods'] = get_submodules(obj)
    var['classes'], var['allclasses'] = get_members(obj, 'class')
    var['exceptions'], var['allexceptions'] = get_members(obj, 'exception')
    var['functions'], var['allfunctions'] = get_members(obj, 'function')
    var['data'], var['alldata'] = get_members(obj, 'data')
    var['members'] = get_members(obj, 'members')
    log.debug('Created context: %s', var)
    return var


def create_module_file(env, package, module, opts):
    """Build the text of the file and write the file."""
    log.debug('Create module file: package %s, module %s', package, module)
    template_file = 'gendoc_module.rst'
    template = env.get_template(template_file)
    fn = makename(package, module)
    var = get_context(package, module, fn)
    var['ispkg'] = False
    rendered = template.render(var)
    write_file(makename(package, module), rendered, opts)


def create_package_file(env, root, master_package, subroot, py_files, opts, subs):
    """Build the text of the file and write the file."""
    log.debug('Create package file: root %s, masterpackage %s, subroot %s', root, master_package, subroot)
    template_file = 'gendoc_package.rst'
    template = env.get_template(template_file)
    fn = makename(master_package, subroot)
    var = get_context(master_package, subroot, fn)
    var['ispkg'] = True
    for submod in var['submods']:
        if shall_skip(submod, opts):
            continue
        create_module_file(env, fn, submod, opts)
    rendered = template.render(var)
    write_file(fn, rendered, opts)


def shall_skip(module, opts):
    """Check if we want to skip this module."""
    log.debug('Testing if %s should be skipped. %r', module)
    # skip if it has a "private" name and this is selected
    if module != '__init__.py' and module.startswith('_') and \
        not opts.includeprivate:
        log.debug('Skip %s because its either private.', module)
        return True
    log.debug('Do not skip %s', module)
    return False


def recurse_tree(env, rootpath, excludes, opts):
    """
    Look for every file in the directory tree and create the corresponding
    ReST files.
    """
    # check if the base directory is a package and get its name
    if INITPY in os.listdir(rootpath):
        root_package = rootpath.split(path.sep)[-1]
    else:
        # otherwise, the base is a directory with packages
        root_package = None

    toplevels = []
    followlinks = getattr(opts, 'followlinks', False)
    includeprivate = getattr(opts, 'includeprivate', False)
    for root, subs, files in walk(rootpath, followlinks=followlinks):
        # document only Python module files (that aren't excluded)
        py_files = sorted(f for f in files
                          if path.splitext(f)[1] in PY_SUFFIXES and
                          not is_excluded(path.join(root, f), excludes))
        is_pkg = INITPY in py_files
        if is_pkg:
            py_files.remove(INITPY)
            py_files.insert(0, INITPY)
        elif root != rootpath:
            # only accept non-package at toplevel
            del subs[:]
            return
        # remove hidden ('.') and private ('_') directories, as well as
        # excluded dirs
        if includeprivate:
            exclude_prefixes = ('.',)
        else:
            exclude_prefixes = ('.', '_')
        subs[:] = sorted(sub for sub in subs if not sub.startswith(exclude_prefixes)
                         and not is_excluded(path.join(root, sub), excludes))

        if is_pkg:
            # we are in a package with something to document
            if subs or len(py_files) > 1 or not \
                shall_skip(path.join(root, INITPY), opts):
                subpackage = root[len(rootpath):].lstrip(path.sep).\
                    replace(path.sep, '.')
                create_package_file(env, root, root_package, subpackage,
                                    py_files, opts, subs)
                toplevels.append(makename(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == rootpath and root_package is None
            for py_file in py_files:
                if not shall_skip(path.join(rootpath, py_file), opts):
                    module = path.splitext(py_file)[0]
                    create_module_file(env, root_package, module, opts)
                    toplevels.append(module)
    return toplevels


def normalize_excludes(rootpath, excludes):
    """Normalize the excluded directory list."""
    return [path.normpath(path.abspath(exclude)) for exclude in excludes]


def is_excluded(root, excludes):
    """Check if the directory is in the exclude list.

    Note: by having trailing slashes, we avoid common prefix issues, like
          e.g. an exlude "foo" also accidentally excluding "foobar".
    """
    root = path.normpath(root)
    for exclude in excludes:
        if root == exclude:
            return True
    return False


def setup_parser():
    """Sets up the argument parser and returns it

    :returns: the parser
    :rtype: :class:`optparse.OptionParser`
    :raises: None
    """
    parser = optparse.OptionParser(
        usage="""\
usage: %prog [options] -o <output_path> <module_path> [exclude_path, ...]

Look recursively in <module_path> for Python modules and packages and create
one reST file with automodule directives per package in the <output_path>.

The <exclude_path>s can be files and/or directories that will be excluded
from generation.

Note: By default this script will not overwrite already created files.""")

    parser.add_option('-o', '--output-dir', action='store', dest='destdir',
                      help='Directory to place all output', default='')
    parser.add_option('-d', '--maxdepth', action='store', dest='maxdepth',
                      help='Maximum depth of submodules to show in the TOC '
                      '(default: 4)', type='int', default=4)
    parser.add_option('-f', '--force', action='store_true', dest='force',
                      help='Overwrite existing files')
    parser.add_option('-l', '--follow-links', action='store_true',
                      dest='followlinks', default=False,
                      help='Follow symbolic links. Powerful when combined '
                      'with collective.recipe.omelette.')
    parser.add_option('-n', '--dry-run', action='store_true', dest='dryrun',
                      help='Run the script without creating files')
    parser.add_option('-P', '--private', action='store_true',
                      dest='includeprivate',
                      help='Include "_private" modules')
    parser.add_option('-s', '--suffix', action='store', dest='suffix',
                      help='file suffix (default: rst)', default='rst')
    parser.add_option('-F', '--full', action='store_true', dest='full',
                      help='Generate a full project with sphinx-quickstart')
    parser.add_option('-H', '--doc-project', action='store', dest='header',
                      help='Project name (default: root module name)')
    parser.add_option('-A', '--doc-author', action='store', dest='author',
                      type='str',
                      help='Project author(s), used when --full is given')
    parser.add_option('-V', '--doc-version', action='store', dest='version',
                      help='Project version, used when --full is given')
    parser.add_option('-R', '--doc-release', action='store', dest='release',
                      help='Project release, used when --full is given, '
                      'defaults to --doc-version')
    return parser


def main(argv=sys.argv):
    """Parse and check the command line arguments."""
    parser = setup_parser()

    (opts, args) = parser.parse_args(argv[1:])

    if not args:
        parser.error('A package path is required.')

    rootpath, excludes = args[0], args[1:]
    if not opts.destdir:
        parser.error('An output directory is required.')
    if opts.header is None:
        opts.header = path.normpath(rootpath).split(path.sep)[-1]
    if opts.suffix.startswith('.'):
        opts.suffix = opts.suffix[1:]
    if not path.isdir(rootpath):
        print >>sys.stderr, '%s is not a directory.' % rootpath
        sys.exit(1)
    if not path.isdir(opts.destdir):
        if not opts.dryrun:
            os.makedirs(opts.destdir)
    rootpath = path.normpath(path.abspath(rootpath))
    excludes = normalize_excludes(rootpath, excludes)
    loader = make_loader()
    env = make_environment(loader)
    modules = recurse_tree(env, rootpath, excludes, opts)
    if opts.full:
        from sphinx import quickstart as qs
        modules.sort()
        prev_module = ''
        text = ''
        for module in modules:
            if module.startswith(prev_module + '.'):
                continue
            prev_module = module
            text += '   %s\n' % module
        d = dict(
            path = opts.destdir,
            sep  = False,
            dot  = '_',
            project = opts.header,
            author = opts.author or 'Author',
            version = opts.version or '',
            release = opts.release or opts.version or '',
            suffix = '.' + opts.suffix,
            master = 'index',
            epub = True,
            ext_autodoc = True,
            ext_viewcode = True,
            makefile = True,
            batchfile = True,
            mastertocmaxdepth = opts.maxdepth,
            mastertoctree = text,
        )
        if not opts.dryrun:
            qs.generate(d, silent=True, overwrite=opts.force)


if __name__ == "__main__":
    main()
