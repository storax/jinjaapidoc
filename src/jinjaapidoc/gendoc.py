#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is a modification of sphinx.apidoc by David.Zuber.
It uses jinja templates to render the rst files.

Parses a directory tree looking for Python modules and packages and creates
ReST files appropriately to create code documentation with Sphinx.

This is derived form the "sphinx-apidoc" script, which is:

  Copyright 2007-2014 by the Sphinx team, see http://sphinx-doc.org/latest/authors.html.
"""
import os
import inspect
import pkgutil
import pkg_resources
import shutil

import jinja2
from sphinx.util.osutil import walk
from sphinx.ext import autosummary


INITPY = '__init__.py'
PY_SUFFIXES = set(['.py', '.pyx'])
TEMPLATE_DIR = 'templates'
"""Built-in template dir for jinjaapi rendering"""
AUTOSUMMARYTEMPLATE_DIR = 'autosummarytemplates'
"""Templates for autosummary"""
MODULE_TEMPLATE_NAME = 'jinjaapi_module.rst'
"""Name of the template that is used for rendering modules."""
PACKAGE_TEMPLATE_NAME = 'jinjaapi_package.rst'
"""Name of the template that is used for rendering packages."""


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


def make_loader(template_dirs):
    """Return a new :class:`jinja2.FileSystemLoader` that uses the template_dirs

    :param template_dirs: directories to search for templates
    :type template_dirs: None | :class:`list`
    :returns: a new loader
    :rtype: :class:`jinja2.FileSystemLoader`
    :raises: None
    """
    return jinja2.FileSystemLoader(searchpath=template_dirs)


def make_environment(loader):
    """Return a new :class:`jinja2.Environment` with the given loader

    :param loader: a jinja2 loader
    :type loader: :class:`jinja2.BaseLoader`
    :returns: a new environment
    :rtype: :class:`jinja2.Environment`
    :raises: None
    """
    return jinja2.Environment(loader=loader)


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


def write_file(app, name, text, dest, suffix, dryrun, force):
    """Write the output file for module/package <name>.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
        app.info('Would create file %s.' % fname)
        return
    if not force and os.path.isfile(fname):
        app.info('File %s already exists, skipping.' % fname)
    else:
        app.info('Creating file %s.' % fname)
        f = open(fname, 'w')
        try:
            f.write(text)
            relpath = os.path.relpath(fname, start=app.env.srcdir)
            abspath = os.sep + relpath
            docpath = app.env.relfn2path(abspath)[0]
            docpath = docpath.rsplit(os.path.extsep, 1)[0]
            app.debug2('Adding document %s' % docpath)
            app.env.found_docs.add(docpath)
        finally:
            f.close()


def import_name(app, name):
    """Import the given name and return name, obj, parent, mod_name

    :param name: name to import
    :type name: str
    :returns: the imported object or None
    :rtype: object | None
    :raises: None
    """
    try:
        app.debug2('Importing %r', name)
        name, obj = autosummary.import_by_name(name)[:2]
        app.debug2('Imported %s', obj)
        return obj
    except ImportError as e:
        app.warn("Jinjapidoc failed to import %r: %s", name, e)


def get_members(app, mod, typ, include_public=None):
    """Return the memebrs of mod of the given type

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    tests = {'class': lambda x: inspect.isclass(x) and not issubclass(x, BaseException) and x.__module__ == mod.__name__,
             'function': lambda x: inspect.isfunction(x) and x.__module__ == mod.__name__,
             'exception': lambda x: inspect.isclass(x) and issubclass(x, BaseException) and x.__module__ == mod.__name__,
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
    app.debug2('Got members of %s of type %s: public %s and %s', mod, typ, public, items)
    return public, items


def _get_submodules(app, module):
    """Get all submodules for the given module/package

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    app.debug2('Getting submodules of %s', p)
    l = [(name, ispkg) for loader, name, ispkg in pkgutil.iter_modules(p)]
    app.debug2('Found submodules of %s: %s', module, l)
    return l


def get_submodules(app, module):
    """Get all submodules without packages for the given module/package

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :param module: the module to query or module path
    :type module: module | str
    :returns: list of module names excluding packages
    :rtype: list
    :raises: TypeError
    """
    l = _get_submodules(app, module)
    return [name for name, ispkg in l if not ispkg]


def get_subpackages(app, module):
    """Get all subpackages for the given module/package

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :param module: the module to query or module path
    :type module: module | str
    :returns: list of packages names
    :rtype: list
    :raises: TypeError
    """
    l = _get_submodules(app, module)
    return [name for name, ispkg in l if ispkg]


def get_context(app, package, module, fullname):
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


    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    app.debug2('Creating context for: package %s, module %s, fullname %s', package, module, fullname)
    obj = import_name(app, fullname)
    if not obj:
        for k in ('subpkgs', 'submods', 'classes', 'allclasses',
                  'exceptions', 'allexceptions', 'functions', 'allfunctions',
                  'data', 'alldata', 'memebers'):
            var[k] = []
        return var

    var['subpkgs'] = get_subpackages(app, obj)
    var['submods'] = get_submodules(app, obj)
    var['classes'], var['allclasses'] = get_members(app, obj, 'class')
    var['exceptions'], var['allexceptions'] = get_members(app, obj, 'exception')
    var['functions'], var['allfunctions'] = get_members(app, obj, 'function')
    var['data'], var['alldata'] = get_members(app, obj, 'data')
    var['members'] = get_members(app, obj, 'members')
    app.debug2('Created context: %s', var)
    return var


def create_module_file(app, env, package, module, dest, suffix, dryrun, force):
    """Build the text of the file and write the file.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    app.debug('Create module file: package %s, module %s', package, module)
    template_file = MODULE_TEMPLATE_NAME
    template = env.get_template(template_file)
    fn = makename(package, module)
    var = get_context(app, package, module, fn)
    var['ispkg'] = False
    rendered = template.render(var)
    write_file(app, makename(package, module), rendered, dest, suffix, dryrun, force)


def create_package_file(app, env, root_package, sub_package, private,
                        dest, suffix, dryrun, force):
    """Build the text of the file and write the file.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    app.debug('Create package file: rootpackage %s, sub_package %s', root_package, sub_package)
    template_file = PACKAGE_TEMPLATE_NAME
    template = env.get_template(template_file)
    fn = makename(root_package, sub_package)
    var = get_context(app, root_package, sub_package, fn)
    var['ispkg'] = True
    for submod in var['submods']:
        if shall_skip(app, submod, private):
            continue
        create_module_file(app, env, fn, submod, dest, suffix, dryrun, force)
    rendered = template.render(var)
    write_file(app, fn, rendered, dest, suffix, dryrun, force)


def shall_skip(app, module, private):
    """Check if we want to skip this module.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :param module: the module name
    :type module: :class:`str`
    :param private: True, if privates are allowed
    :type private: :class:`bool`
    """
    app.debug2('Testing if %s should be skipped.', module)
    # skip if it has a "private" name and this is selected
    if module != '__init__.py' and module.startswith('_') and \
       not private:
        app.debug2('Skip %s because its either private or __init__.', module)
        return True
    app.debug2('Do not skip %s', module)
    return False


def recurse_tree(app, env, src, dest, excludes, followlinks, force, dryrun, private, suffix):
    """Look for every file in the directory tree and create the corresponding
    ReST files.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
            continue
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
               shall_skip(app, os.path.join(root, INITPY), private):
                subpackage = root[len(src):].lstrip(os.path.sep).\
                    replace(os.path.sep, '.')
                create_package_file(app, env, root_package, subpackage,
                                    private, dest, suffix, dryrun, force)
                toplevels.append(makename(root_package, subpackage))
        else:
            # if we are at the root level, we don't require it to be a package
            assert root == src and root_package is None
            for py_file in py_files:
                if not shall_skip(app, os.path.join(src, py_file), private):
                    module = os.path.splitext(py_file)[0]
                    create_module_file(app, env, root_package, module, dest, suffix, dryrun, force)
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


def generate(app, src, dest, exclude=[], followlinks=False,
             force=False, dryrun=False, private=False, suffix='rst',
             template_dirs=None):
    """Generage the rst files

    Raises an :class:`OSError` if the source path is not a directory.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
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
    :param template_dirs: directories to search for user templates
    :type template_dirs: None | :class:`list`
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
    loader = make_loader(template_dirs)
    env = make_environment(loader)
    recurse_tree(app, env, src, dest, exclude, followlinks, force, dryrun, private, suffix)


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

    # for Sphinx 1.3
    suffix = c.source_suffix[0] if isinstance(c.source_suffix, list) else c.source_suffix

    out = c.jinjaapi_outputdir or app.env.srcdir

    if c.jinjaapi_addsummarytemplate:
        tpath = pkg_resources.resource_filename(__package__, AUTOSUMMARYTEMPLATE_DIR)
        c.templates_path.append(tpath)

    tpath = pkg_resources.resource_filename(__package__, TEMPLATE_DIR)
    c.templates_path.append(tpath)

    prepare_dir(app, out, not c.jinjaapi_nodelete)
    generate(app, src, out,
             exclude=c.jinjaapi_exclude_paths,
             force=c.jinjaapi_force,
             followlinks=c.jinjaapi_followlinks,
             dryrun=c.jinjaapi_dryrun,
             private=c.jinjaapi_includeprivate,
             suffix=suffix,
             template_dirs=c.templates_path)
