import os

here = os.path.abspath(os.path.dirname(__file__))

extensions = [
    'sphinx.ext.viewcode',
    'jinjaapidoc',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'Jinja Api Test'
copyright = u'2015, David Zuber'

version = '0.1.0'

release = '0.1.0'

exclude_patterns = []

pygments_style = 'sphinx'

html_theme = 'classic'

html_static_path = ['_static']

htmlhelp_basename = 'JinjaApiTestdoc'

autosummary_generate = True

jinjaapi_outputdir = os.path.join(here, 'jinjaapiout')
jinjaapi_srcdir = os.path.abspath(os.path.join(here, '..', '..', '..', 'src'))
