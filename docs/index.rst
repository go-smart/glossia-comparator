.. Glossia documentation master file, created by
   sphinx-quickstart on Mon Mar 28 11:39:05 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Glossia
=======
Go-Smart Simulation Architecture (aka. GSSA)
--------------------------------------------

Contents:

.. toctree::
   :maxdepth: 2

   Comparison <comparison.md>
   Errors <errors.md>
   GSSA XML Format <gssa-xml.md>
   Families<families.md>
   Clinical Domain Model <cdm/index.rst>
   Server <server/index.rst>
   Docker Workflows <docker/index.rst>
   API <api/modules.rst>
   Documentation <docs.md>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


| **Primary authors** : `NUMA Engineering Services Ltd <http://www.numa.ie>`_ (NUMA), Dundalk, Ireland
| **Project website** : `http://www.gosmart-project.eu/ <http://www.gosmart-project.eu/>`_

This project is co-funded by the European Commission under grant agreement no. 600641.

This tool, GSSA, provides scripts for running a generic simulation server, with support for Docker-based webuser-configurable simulation tools, and the configuration for the `Crossbar.io <https://crossbar.io>`_ WAMP router.

Dependencies
------------

* Python 2.7
* Python 3
* `Elmer (with NUMA modifications) <https://github.com/go-smart/gssf-elmer>`_
* GMSH
* VTK 5.8
* libjsoncpp-dev
* (Python 3) munkres pyyaml
* (Python 2) PythonOCC

Installation
------------

CMake installation is recommended from an out-of-source build directory.

Usage
-----

The simulation workflow may be launched by the command

.. code-block:: sh

  go-smart-launcher settings.xml
..

where `settings.xml` is a GSSF-XML file. Adding --help will show documentation of command line arguments.
