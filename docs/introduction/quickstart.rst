Quickstart
==========

The intended setup for using Glossia is as a containerized
process, with access to the host's Docker daemon only via
the `dockerlaunch <https://go-smart.github.io/dockerlaunch>`_
system.

Dependencies
------------

- dockerlaunch
  (`installation guide <https://go-smart.github.io/dockerlaunch/installation>`_)
- pip (Ubuntu: ``sudo apt-get install python-pip``)
- docker-compose (``sudo pip install docker-compose``)


Execution
---------

The Glossia server may be launched as follows:

.. code-block:: bash

    git clone https://github.com/go-smart/glossia-server-side
    cd glossia-server-side
    sudo ./setup.sh
    sudo ./start-local.sh

This will start both a WAMP router and a Docker instance connected
to it. Any client supporting Glossia may connect to it on your
local machine at port 8080.

**You should ensure that only authorized clients may access the
router port.** Moreover, note that WAMP traffic and responses
are not secure between clients attached to the same WAMP router.

Adding simulation containers
----------------------------

Simulation container images may be pulled in using the command:

.. code-block:: bash

    sudo docker pull gosmart/glossia-goosefoot

This enables the `Goosefoot <https://go-smart.github.io/goosefoot>`_
family workflow, wrapping `CGAL <http://www.cgal.org/>`_
and the `Elmer <https://www.csc.fi/web/elmer>`_ solver.

Another available image is ``gosmart/glossia-fenics``,
wrapping the `FEniCS <http://fenicsproject.org>`_ libraries.
This package is very well-suited to Glossia usage, and adapting
FEniCS Python codes to Glossia is especially straightforward.

Glossia does not need to be restarted to use these images - as long
as Glossia has the relevant family built in and dockerlaunch has the image
whitelisted, any subsequent GSSA-XML definitions using the image
should run as normal.

Interaction
-----------

The current stable Glossia clients are `Glot <https://go-smart.github.io/glot>`_ and
the `Go-Smart Web Framework <https://smart-mict.eu/>`_. Glot is the core
technology for simulation developer use and testing, and is intended
to be comprehensive.
An open source, proof-of-concept
web-based management tool also exists, but should not be considered
ready for use.

If you would be
interested in using the radiological interface for your own projects,
or sponsoring development of the developer-friendly open source simulation
management tool,
please contact the `Go-Smart Consortium <https://gosmart-project.eu/>`_.
