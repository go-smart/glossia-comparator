# Go-Smart Simulation Architecture (GSSA)

**Primary authors** : `NUMA Engineering Services Ltd <http://www.numa.ie>`_ (NUMA), Dundalk, Ireland<br/>
**Project website** : `http://www.gosmart-project.eu/ <http://www.gosmart-project.eu/>`_

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

```sh
  go-smart-launcher settings.xml
```

where `settings.xml` is a GSSF-XML file. Adding --help will show documentation of command line arguments.
