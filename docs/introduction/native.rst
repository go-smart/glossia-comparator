Native Installation
===================

In general, it is recommended to use Glossia within a Docker container
and it has been designed with this usage in mind.
See the `Quickstart <quickstart>`_ documentation for further detail.
However, if you do want to install Glossia separately on a host, for
development or testing, these instructions apply. If you have difficulty
you may still find comparing with the Dockerfile useful, as it
comprises a verifiable list of instructions for Glossia installation
on an Ubuntu base.

Dependencies
------------

* `dockerlaunch <https://go-smart.github.io/dockerlaunch>`_
* Python 2.7
* Python 3
* `Elmer (with NUMA modifications) <https://github.com/go-smart/gssf-elmer>`_
* GMSH
* VTK 5.8
* libjsoncpp-dev
* (Python 3) munkres pyyaml
* (Python 2) PythonOCC

Building
--------

CMake installation is recommended from an out-of-source build directory.

.. code-block:: sh

  git clone https://github.io/go-smart/glossia.git
  mkdir glossia-build
  cd glossia-build
  cmake ../glossia-build -DCMAKE_INSTALL_PREFIX=$INSTALLATION_TARGET
  make
  make install

The ``$INSTALLATION_TARGET`` may be ``~/.local`` for per-user testing or
the entire ``CMAKE_INSTALL_PREFIX`` argument may be omitted for system-wide
installation.

Usage
-----

Make sure ``dockerlaunchd`` has been started.
The simulation server may be launched by the command

.. code-block:: sh

  go-smart-simulation-server --host $WAMP_ROUTER \
    --websocket-port 8080 $CHOSEN_SERVER_NAME

This will register WAMP end-points onto the router at ``$WAMP_ROUTER`` via port ``8080``.
The ``$CHOSEN_SERVER_NAME`` is an identifier that allows persistence of Glossia data within
the current directory, so that existing simulation records will be available on restart. It
is also supplied to the WAMP router to enable server-specific commands to be issued.
