Glossia
=======

Go-Smart Simulation Architecture (aka. GSSA)
--------------------------------------------

Glossia is a standalone set of tools for simulation orchestration, allowing remote control of
computational numerics software in Docker containers. It is administrated via WAMP and
simulations are configured using [GSSA-XML](reference/gssa-xml.rst), a conceptual description
format facilitating easy interchange of physical model components around a numerical model.

The framework is used to provide a simulation backend for the [Go-Smart](http://smart-mict.eu/)
web-based Minimally Invasive Cancer Treatment (MICT) platform. Using this technology, researchers
and technicians can dynamically alter simulation strategies and equipment/physical parameters
through the web-interface.

While existing technologies allow hypermodel modification through
tools such as [Apache Taverna](http://incubator.apache.org/projects/taverna.html), Go-Smart, through
Glossia, is unusual in that it provides interactive support for collaborative simulation at a
hypomodel level. At present, this is tested within a small number of frameworks (corresponding
to container images) including Python/Numpy/[FEniCS](https://fenicsproject.org) and
[Elmer](https://www.csc.fi/web/elmer).

- **Primary authors** : [NUMA Engineering Services Ltd](http://www.numa.ie>) (NUMA), Dundalk, Ireland
- **Project website** : [http://www.gosmart-project.eu/](http://www.gosmart-project.eu/)

This project is co-funded by the European Commission under grant agreement no. 600641.

Documentation
-------------

Documentation for this component is available at
<https://go-smart.github.io/gssa>

Installation
------------

CMake installation is recommended from an out-of-source build directory.

Usage
-----

The simulation server (GSSA) may be launched by the command

``` {.sourceCode .sh}
crossbar --debug start --cbdir path/to/directory(web)[default gssf-release/web]
go-smart-simulation-server --host HOSTADDRESS/localhost --websocket-port PORTNUMBER
go-smart-simulation-client --gssa-file XMLFILE --websocket-port PORTNUMBER --host HOSTADDRESS/localhost --definitions path/to/file.py --skip-clean --output Lesion.vtp
```

Adding --help will show documentation of command line arguments. You
should start Crossbar.io in the gssf/web directory of the build folder
before launching this script. Ensure that the configuration in the web
directory matches the port and host to which go-smart-simulation-server
will connect for WAMP interaction.
