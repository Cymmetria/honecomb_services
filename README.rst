|GitHub license| |PyPI| |Read the Docs| |Travis| |Updates| |Codecov|

.. |GitHub license| image:: https://img.shields.io/github/license/Cymmetria/honeycomb_plugins.svg
   :alt: GitHub license
   :target: https://github.com/Cymmetria/honeycomb_plugins/blob/master/LICENSE
.. |Read the Docs| image:: https://img.shields.io/readthedocs/honeycomb_plugins.svg
   :alt: Read the Docs
   :target: http://honeycomb_plugins.cymmetria.com
.. |Travis| image:: https://img.shields.io/travis/Cymmetria/honeycomb_plugins.svg
   :alt: Travis
   :target: https://travis-ci.org/Cymmetria/honeycomb_plugins
.. |Updates| image:: https://pyup.io/repos/github/Cymmetria/honeycomb/shield.svg
    :target: https://pyup.io/repos/github/Cymmetria/honeycomb_plugins/
    :alt: Updates
.. |Codecov| image:: https://img.shields.io/codecov/c/github/Cymmetria/honeycomb_plugins.svg
   :alt: Codecov
   :target: https://codecov.io/gh/Cymmetria/honeycomb_plugins


Honeycomb - An extensible honeypot framework
============================================

Honeycomb is an open-source honeypot framework created by Cymmetria_.

.. _Cymmetria: https://cymmetria.com

Honeycomb allows running honeypots with various integrations from a public library of plugins from https://github.com/Cymmetria/honeycomb_plugins

Writing new honeypot services and integrations for honeycomb is super easy!
See the plugins repo for more info.

Full CLI documentation can be found at http://honeycomb.cymmetria.com/en/latest/cli.html

Usage
-----

Using pip::

    $ pip install honeycomb-framework
    $ honeycomb --help

Using Docker::

    $ docker run -v honeycomb.yml:/usr/share/honeycomb/honeycomb.yml cymmetria/honeycomb
