#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is a modification of sphinx.apidoc by David.Zuber
It uses jinja templates to render the rst files.

Parses a directory tree looking for Python modules and packages and creates
ReST files appropriately to create code documentation with Sphinx.

This is derived form the "sphinx-apidoc" script, which is:
Copyright 2007-2014 by the Sphinx team, see http://sphinx-doc.org/latest/authors.html.
"""
import os
import inspect
import pkgutil
import logging

import jinja2
from sphinx.util.osutil import walk
from sphinx.ext import autosummary

log = logging.getLogger(__name__)

INITPY = '__init__.py'
PY_SUFFIXES = set(['.py', '.pyx'])
TEMPLATE_DIR = 'templates'


def make_loader(template_dirs=None):
    """Return a new :class:`jinja2.FileSystemLoader` that uses the template_dirs or
    a :class:`jinja2.PackageLoader` with the default packages

    :param template_dirs: searchpath for templates.
    :type template_dirs: list | None
    :returns: a new loader
    :rtype: :class:`jinja2.BaseLoader`
    :raises: None
    """
    if template_dirs:
        log.debug('Creating loader with template dirs: %s', template_dirs)
        return jinja2.FileSystemLoader(searchpath=template_dirs)
    else:
        log.debug('Creating package loader with default templates.')
        return jinja2.PackageLoader(__package__, TEMPLATE_DIR)


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
    """Join package and module with a dot.

    Package or Module can be empty.

    :param package: the package name
    :type package: :class:`str`
    :param module: the module name
    :type module: :class:`str`
    :returns: the joined name
    :rtype: :class:`str`
    :raises: :class:`AssertionError`, if both package and module are empty
    """
    # Both package and module can be None/empty.
    assert package or module, "Specify either package or module"
    if package:
        name = package
        if module:
            name += '.' + module
    else:
        name = module
    return name


def write_file(name, text, dest, suffix, dryrun, force):
    """Write the output file for module/package <name>.

    :param name: the file name without file extension
    :type name: :class:`str`
    :param text: the content of the file
    :type text: :class:`str`
    :param dest: the output directory
    :type dest: :class:`str`
    :param suffix: the file extension
    :type suffix: :class:`str`
    :param dryrun: If True, do not create any files, just log the potential location.
    :type dryrun: :class:`bool`
    :param force: Overwrite existing files
    :type force: :class:`bool`
    :returns: None
    :raises: None
    """
    fname = os.path.join(dest, '%s.%s' % (name, suffix))
    if dryrun:
        log.info('Would create file %s.', fname)
        return
    if not force and os.path.isfile(fname):
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


def create_module_file(env, package, module, dest, suffix, dryrun, force):
    """Build the text of the file and write the file.

    :param env: the jinja environment for the templates
    :type env: :class:`jinja2.Environment`
    :param package: the package name
    :type package: :class:`str`
    :param module: the module name
    :type module: :class:`str`
    :param dest: the output directory
    :type dest: :class:`str`
    :param suffix: the file extension
    :type suffix: :class:`str`
    :param dryrun: If True, do not create any files, just log the potential location.
    :type dryrun: :class:`bool`
    :param force: Overwrite existing files
    :type force: :class:`bool`
    :returns: None
    :raises: None
    """
    log.debug('Create module file: package %s, module %s', package, module)
    template_file = 'module.rst'
    template = env.get_template(template_file)
    fn = makename(package, module)
    var = get_context(package, module, fn)
    var['ispkg'] = False
    rendered = template.render(var)
    write_file(makename(package, module), rendered, dest, suffix, dryrun, force)


def create_package_file(env, root_package, sub_package, private, dest, suffix, dryrun, force):
    """Build the text of the file and write the file.

    :param env: the jinja environment for the templates
    :type env: :class:`jinja2.Environment`
    :param root_package: the parent package
    :type root_package: :class:`str`
    :param sub_package: the package name without root
    :type sub_package: :class:`str`
    :param private: Include \"_private\" modules
    :type private: :class:`bool`
    :param dest: the output directory
    :type dest: :class:`str`
    :param suffix: the file extension
    :type suffix: :class:`str`
    :param dryrun: If True, do not create any files, just log the potential location.
    :type dryrun: :class:`bool`
    :param force: Overwrite existing files
    :type force: :class:`bool`
    :returns: None
    :raises: None
    """
    log.debug('Create package file: rootpackage %s, sub_package %s', root_package, sub_package)
    template_file = 'package.rst'
    template = env.get_template(template_file)
    fn = makename(root_package, sub_package)
    var = get_context(root_package, sub_package, fn)
    var['ispkg'] = True
    for submod in var['submods']:
        if shall_skip(submod, private):
            continue
        create_module_file(env, fn, submod, suffix, dryrun, force)
    rendered = template.render(var)
    write_file(fn, rendered, dest, suffix, dryrun, force)


def shall_skip(module, private):
    """Check if we want to skip this module.

    :param module: the module name
    :type module: :class:`str`
    :param private: True, if privates are allowed
    :type private: :class:`bool`
    """
    log.debug('Testing if %s should be skipped. %r', module)
    # skip if it has a "private" name and this is selected
    if module != '__init__.py' and module.startswith('_') and \
        not private:
        log.debug('Skip %s because its either private or __init__.', module)
        return True
    log.debug('Do not skip %s', module)
    return False


def recurse_tree(env, src, dest, excludes, followlinks, force, dryrun, private, suffix):
    """Look for every file in the directory tree and create the corresponding
    ReST files.

    :param env: the jinja environment
    :type env: :class:`jinja2.Environment`
    :param src: the path to the python source files
    :type src: :class:`str`
    :param dest: the output directory
    :type dest: :class:`str`
    :param excludes: the paths to exclude
    :type excludes: :class:`list`
    :param followlinks: follow symbolic links
    :type followlinks: :class:`bool`
    :param force: overwrite existing files
    :type force: :class:`bool`
    :param dryrun: do not generate files
    :type dryrun: :class:`bool`
    :param private: include "_private" modules
    :type private: :class:`bool`
    :param suffix: the file extension
    :type suffix: :class:`str`
    """
    # check if the base directory is a package and get its name
    if INITPY in os.listdir(src):
        root_package = src.split(os.path.sep)[-1]
    else:
        # otherwise, the base is a directory with packages
        root_package = None

    toplevels = []
    for root, subs, files in walk(src, followlinks=followlinks):
        # document only Python module files (that aren't excluded)
        py_files = sorted(f for f in files
                          if os.path.splitext(f)[1] in PY_SUFFIXES and
                          not is_excluded(os.path.join(root, f), excludes))
        is_pkg = INITPY in py_files
        if is_pkg:
            py_files.remove(INITPY)
            py_files.insert(0, INITPY)
        elif root != src:
            # only accept non-package at toplevel
            del subs[:]
            return
        # remove hidden ('.') and private ('_') directories, as well as
        # excluded dirs
        if private:
            exclude_prefixes = ('.',)
        else:
            exclude_prefixes = ('.', '_')
        subs[:] = sorted(sub for sub in subs if not sub.startswith(exclude_prefixes)
                         and not is_excluded(os.path.join(root, sub), excludes))

        if is_pkg:
            # we are in a package with something to document
            if subs or len(py_files) > 1 or not \
                shall_skip(os.path.join(root, INITPY), private):
                subpackage = root[len(src):].lstrip(os.path.sep).\
                    replace(os.path.sep, '.')
                create_package_file(env, root_package, subpackage,
                                    private, dest, suffix, dryrun, force)
                toplevels.append(makename(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == src and root_package is None
            for py_file in py_files:
                if not shall_skip(os.path.join(src, py_file), private):
                    module = os.path.splitext(py_file)[0]
                    create_module_file(env, root_package, module, dest, suffix, dryrun, force)
                    toplevels.append(module)
    return toplevels


def normalize_excludes(excludes):
    """Normalize the excluded directory list."""
    return [os.path.normpath(os.path.abspath(exclude)) for exclude in excludes]


def is_excluded(root, excludes):
    """Check if the directory is in the exclude list.

    Note: by having trailing slashes, we avoid common prefix issues, like
          e.g. an exlude "foo" also accidentally excluding "foobar".
    """
    root = os.path.normpath(root)
    for exclude in excludes:
        if root == exclude:
            return True
    return False


def generate(self, src, dest, exclude=[], followlinks=False, force=False, dryrun=False, private=False, suffix='rst'):
    """Generage the rst files

    Raises an :class:`OSError` if the source path is not a directory.

    :param src: path to python source files
    :type src: :class:`str`
    :param dest: output directory
    :type dest: :class:`str`
    :param exclude: list of paths to exclude
    :type exclude: :class:`list`
    :param followlinks: follow symbolic links
    :type followlinks: :class:`bool`
    :param force: overwrite existing files
    :type force: :class:`bool`
    :param dryrun: do not create any files
    :type dryrun: :class:`bool`
    :param private: include \"_private\" modules
    :type private: :class:`bool`
    :param suffix: file suffix
    :type suffix: :class:`str`
    :returns: None
    :rtype: None
    :raises: OSError
    """
    suffix = suffix.strip('.')
    if not os.path.isdir(src):
        raise OSError("%s is not a directory" % src)
    if not os.path.isdir(dest) and not dryrun:
        os.makedirs(dest)
    src = os.path.normpath(os.path.abspath(src))
    exclude = normalize_excludes(exclude)
    loader = make_loader()
    env = make_environment(loader)
    recurse_tree(env, src, dest, exclude, followlinks, force, dryrun, private, suffix)