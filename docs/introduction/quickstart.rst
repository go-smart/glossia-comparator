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
