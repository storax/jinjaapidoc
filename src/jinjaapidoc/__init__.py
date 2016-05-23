__author__ = 'David Zuber'
__email__ = 'zuber.david@gmx.de'
__version__ = '0.3.1'


import jinjaapidoc.ext as ext
import jinjaapidoc.gendoc as gendoc


def setup(app):
    """Setup the sphinx extension

    This will setup autodoc and autosummary.
    Add the :class:`ext.ModDocstringDocumenter`.
    Add the config values.
    Connect builder-inited event to :func:`gendoc.main`.

    :param app: the sphinx app
    :type app: :class:`sphinx.application.Sphinx`
    :returns: None
    :rtype: None
    :raises: None
    """
    # Connect before autosummary
    app.connect('builder-inited', gendoc.main)

    app.setup_extension('sphinx.ext.autodoc')
    app.setup_extension('sphinx.ext.autosummary')

    app.add_autodocumenter(ext.ModDocstringDocumenter)

    app.add_config_value('jinjaapi_outputdir', '', 'env')
    app.add_config_value('jinjaapi_nodelete', True, 'env')
    app.add_config_value('jinjaapi_srcdir', '', 'env')
    app.add_config_value('jinjaapi_exclude_paths', [], 'env')
    app.add_config_value('jinjaapi_force', True, 'env')
    app.add_config_value('jinjaapi_followlinks', True, 'env')
    app.add_config_value('jinjaapi_dryrun', False, 'env')
    app.add_config_value('jinjaapi_includeprivate', True, 'env')
    app.add_config_value('jinjaapi_addsummarytemplate', True, 'env')

    return {'version': __version__, 'parallel_read_safe': True}
