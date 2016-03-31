Introduction
============

Glossia provides simulation orchestration - that is, it allows a WAMP client to send new simulations,
defined in the `GSSA-XML <../reference/gssa-xml>`_ format, then monitor progress, cancel or retrieve diagnostic
data from these simulations. The `GSSA-XML`_ format is designed to abstract parameters from a numerical model,
and allow simple interchange of both models, parameters and input data such as geometric information.

The framework is used to provide a simulation backend for the `Go-Smart <http://smart-mict.eu/>`_
web-based Minimally Invasive Cancer Treatment (MICT) platform. Using this technology, researchers
and technicians can dynamically alter simulation strategies and equipment/physical parameters
through the web-interface. For more information about this project, see
`http://www.gosmart-project.eu/ <http://www.gosmart-project.eu/>`_.

.. toctree::
    quickstart
    native
