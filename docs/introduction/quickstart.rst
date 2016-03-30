Quickstart
==========

The intended setup for using Glossia is as a containerized
process, with access to the host's Docker daemon only via
the `dockerlaunch <https://go-smart.github.io/dockerlaunch>`_
system.

First, install and start dockerlaunch
(`installation guide <https://go-smart.github.io/dockerlaunch/installation>`_).

The Glossia server may be launched in only a few commands:

.. code-block:: bash

    git clone https://github.io/go-smart/glossia-server-side
    cd glossia-server-side
    sudo ./setup.sh
    sudo ./start-local.sh

This will start both a WAMP router and a Docker instance connected
to it. Any client supporting Glossia may connect to it on your
local machine at port 8080.
