Glossia (aka. GSSA)
===================

The Go-Smart Simulation Architecture
------------------------------------

**Primary authors** : [NUMA Engineering Services
Ltd](http://www.numa.ie) (NUMA), Dundalk, Ireland

**Project website** : <http://www.gosmart-project.eu/>

This project is co-funded by: European Commission under grant agreement
no. 600641.

This tool, GSSA, provides scripts for running a generic simulation
server, with support for Docker-based webuser-configurable simulation
tools, and the configuration for the [Crossbar.io](https://crossbar.io)
WAMP router.

Dependencies
------------

-   Python 3
-   Crossbar.io
-   libjsoncpp-dev
-   (Python 3) munkres pyyaml crossbar docker
-   (Python 2) hachiko paramiko

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
