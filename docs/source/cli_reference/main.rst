CLI Reference
=============

Here you can find the CLI reference for Pyrrowhead.

:ref:`cli-management` describes the commands used to manage an active local cloud, for example adding orchestration rules.
These commands will only change a local cloud during run-time.

:ref:`cli-setup` describes the commands used to set up the static configuration of local clouds and organizations.
These commands are used to create new certificates or add new core systems.
Most of these commands requires a restart of the local clouds to take effect.

The CLI reference can also be found by running any ``pyrrowhead`` command with the ``--help`` option.

.. command-output:: pyrrowhead --help

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   management
   setup