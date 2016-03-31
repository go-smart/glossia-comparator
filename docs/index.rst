.. Glossia documentation master file, created by
   sphinx-quickstart on Mon Mar 28 11:39:05 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Glossia
=======
Go-Smart Simulation Architecture (aka. GSSA)
--------------------------------------------

Glossia is a standalone set of tools for simulation orchestration, allowing remote control of
computational numerics software in Docker containers. It is administrated via WAMP and
simulations are configured using `GSSA-XML <reference/gssa-xml.rst>`_, a conceptual description
format facilitating easy interchange of physical model components around a numerical model.

The framework is used to provide a simulation backend for the `Go-Smart <http://smart-mict.eu/>`_
web-based Minimally Invasive Cancer Treatment (MICT) platform. Using this technology, researchers
and technicians can dynamically alter simulation strategies and equipment/physical parameters
through the web-interface. For more information, our first published work
`Go-Smart: Web-based Computational Modeling of Minimally Invasive Cancer Treatments <http://arxiv.org/abs/1511.03418>`_
provides an overview of the wider project.

While existing technologies allow hypermodel modification through
tools such as `Apache Taverna <http://incubator.apache.org/projects/taverna.html>`_, Go-Smart, through
Glossia, is unusual in that it provides interactive support for collaborative simulation at a
hypomodel level. At present, this is tested within a small number of frameworks (corresponding
to container images) including Python/Numpy/`FEniCS <https://fenicsproject.org>`_ and
`Elmer <https://www.csc.fi/web/elmer>`_.

The current stable Glossia clients are `Glot <https://go-smart.github.io/glot>`_ and
the `Go-Smart Web Framework <https://smart-mict.eu/>`_.

| **Primary authors** : `NUMA Engineering Services Ltd <http://www.numa.ie>`_ (NUMA), Dundalk, Ireland
| **Project website** : `http://www.gosmart-project.eu/ <http://www.gosmart-project.eu/>`_

This project is co-funded by the European Commission under grant agreement no. 600641.


Contents
========

.. toctree::
   :maxdepth: 3

   Home <self>
   Introduction <introduction/index.rst>
   Reference <reference/index.rst>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


