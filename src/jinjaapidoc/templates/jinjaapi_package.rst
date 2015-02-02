{% block header -%}
:mod:`{{ fullname }}`
======={% for c in fullname %}={% endfor %}
{%- endblock %}

{% block subpackages %}{% if subpkgs -%}
Subpackages
-----------
.. toctree::
   :maxdepth: 3
{% for p in subpkgs %}
   {{ fullname }}.{{ p }}
{%- endfor %}{% endif %}{% endblock %}

{% block submodules %}{% if submods -%}
Submodules
----------
.. toctree::
   :maxdepth: 1
{% for m in submods %}
   {{ fullname }}.{{ m }}
{%- endfor %}{% endif %}{% endblock %}

{% block contents %}{% if ispkg -%}
Module contents
---------------
{%- endif %}

.. automoddoconly:: {{ fullname }}

.. currentmodule:: {{ fullname }}

{% block classsummary %}{% if classes -%}
Classes
~~~~~~~

.. autosummary::
   :toctree: {{ fullname }}
{% for c in classes %}
     {{ c }}
{%- endfor %}{% endif %}{% endblock %}

{% block exceptionssummary %}{% if exceptions -%}
Exceptions
~~~~~~~~~~

.. autosummary::
   :toctree: {{ fullname }}
{% for e in exceptions %}
     {{ e }}
{%- endfor %}{% endif %}{% endblock %}

{% block functionsssummary %}{% if functions -%}
Functions
~~~~~~~~~

.. autosummary::
{% for f in functions %}
     {{ f }}
{%- endfor %}{% endif %}{% endblock %}

{% block datasummary %}{% if data -%}
Data
~~~~

.. autosummary::
{% for d in data %}
     {{ d }}
{%- endfor %}{% endif %}{% endblock %}

{% block functionsdoc -%}
{% for f in functions %}
.. autofunction:: {{ f }}
{%- endfor %}{% endblock %}

{% block datadoc -%}
{% for d in data %}
.. autodata:: {{ d}}
{%- endfor %}{% endblock %}{% endblock %}
