"""The sphinx extension"""
from sphinx.ext import autodoc

import jinjaapidoc
import jinjaapidoc.updatedoc as updatedoc


class ModDocstringDocumenter(autodoc.ModuleDocumenter):
    """A documenter for modules which only inserts the docstring of the module."""
    objtype = "moddoconly"

    #do not indent the content
    content_indent = ""

    #do not add a header to the docstring
    def add_directive_header(self, sig):
        """Add the directive header and options to the generated content."""
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', "module")
        name = self.format_name()
        self.add_line(u'.. %s:%s:: %s%s' % (domain, directive, name, sig),
                      '<autodoc>')
        if self.options.noindex:
            self.add_line(u'   :noindex:', '<autodoc>')
        if self.objpath:
            # Be explicit about the module, this is necessary since .. class::
            # etc. don't support a prepended module name
            self.add_line(u'   :module: %s' % self.modname, '<autodoc>')

    def document_members(self, all_members=False):
        pass


def setup(app):
    """Setup the sphinx extension

    This will setup autodoc and autosummary.
    Add the :class:`ModDocstringDocumenter`.
    Add the config values.
    Connect builder-inited event to :func:`updatedoc.main`.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :returns: None
    :rtype: None
    :raises: None
    """
    app.setup_extension('sphinx.ext.autodoc')
    app.setup_extension('sphinx.ext.autosummary')

    app.add_autodocumenter(ModDocstringDocumenter)

    app.add_config_value('jinjaapi_outputdir', '', 'env')
    app.add_config_value('jinjaapi_nodelete', True, 'env')
    app.add_config_value('jinjaapi_srcdir', '', 'env')
    app.add_config_value('jinjaapi_exclude_paths', [], 'env')
    app.add_config_value('jinjaapi_force', True, 'env')
    app.add_config_value('jinjaapi_followlinks', True, 'env')
    app.add_config_value('jinjaapi_dryrun', True, 'env')
    app.add_config_value('jinjaapi_private', True, 'env')
    app.add_config_value('jinjaapi_templatedirs', [], 'env')

    app.connect('builder-inited', updatedoc.main)
    return {'version': jinjaapidoc.__version__, 'parallel_read_safe': True}
