About Pyrrowhead
================

The way Pyrrowhead manages local clouds is not completely obvious, and errors can be somewhat hard to debug.
The CLI commands try to warn users when something has gone wrong, but there are many corner-cases that are yet detected.
This chapter explains how pyrrowhead works internally to help users understand and manually manage the local clouds
when necessary.

.. note::
   The following information *only* applies on Linux systems.

   Pyrrowhead is not tested on MacOS or Windows.

   Any contributions towards enabling support for those platforms are appreciated.

.. warning::
   The internals of Pyrrowhead are subject to change.

Pyrrowhead Home Directory
-------------------------

The first time Pyrrowhead is started it creates new directory ``~/.pyrrowhead`` in the home directory of the currently
running user.
All local cloud information and Pyrrowhead config is stored in this directory.
The directory consists of the ``config.cfg`` file containing Pyrrowhead configuration, and the ``local-clouds`` folder
containing local cloud files.

``config.cfg``
..............

The config file contains two tables, ``pyrrowhead`` and ``local-clouds``.
This file is read upon every CLI call to find the currently active cloud ``pyrrowhead.active-cloud`` and the
location where individual local clouds are installed ``local-clouds.<CLOUD_IDENTIFIER>``.

This example ``config.cfg``

.. code-block::

   [pyrrowhead]
   active-cloud = test.test_corp

   [local-clouds]
   test.test_corp = /home/tester/.pyrrowhead/local-clouds/test_corp/test
   test2.test_corp = /home/tester/.pyrrowhead/local-clouds/test_corp/test2

contains two local clouds, ``test.test_corp`` and ``test2.test_corp``, with the latter being the active local cloud.
The active cloud is the one that will be managed by commands such as ``pyrrowhead services``
and ``pyrrowhead orchestration``.
The active local cloud is set upon starting a local cloud with ``pyrrowhead cloud up``, and is cleared when the local
cloud is stopped with ``pyrrowhead cloud down``.

.. warning::
   Changing any local-cloud information, either the CLOUD_IDENTIFIER or the cloud path will generally
   disable Pyrrowheads ability to set up, manage, and configure that local cloud, unless you specify a location with
   a local cloud installed.

.. _local-cloud-dir:

The ``local-clouds`` Directory
..............................

The local clouds directory is a nested folder structure that organizes organization and cloud level information
in a shared manner.
The general structure looks like this:

.. code-block::

   local-clouds/
   ├─ test_corp/
   │  ├─ org-certs/
   │  ├─ test/
   │  ├─ test2/
   ├─ another_org/

The ``test_corp/`` and ``another_corp/`` are organization directories, containing organization information such as
organization certificates and keys in ``org-certs``, as well as local cloud directories.
The ``test_corp/test/`` and ``test_corp/test2/`` are local cloud directories, which has the following structure:

.. code-block::

   cloud_dir/
   ├─ cloud_config.yaml
   ├─ docker-compose.yml
   ├─ certs/
   │  ├─ crypto/
   ├─ core_system_config/
   ├─ initSQL.sh
   ├─ sql/

.. note::
   A setup but not yet installed local cloud only contains ``cloud_config.yaml``.

The most important file for Pyrrowhead is ``cloud_config.yaml``.
It's the file that contains all information necessary to install the local cloud.
All the other files are generated with the information from that ``cloud_config.yaml``.

The second most important element are the keys and certificates in ``certs/crypto/``.
Each core and client system defined in ``cloud_config.yaml`` will have a corresponding key (``.key``),
certificate (``.pem``), and PKCS#12 file (``.p12``) generated.
If you only want to use Pyrrowhead for the certificates, this is where you can find them.
Just make sure you :ref:`add client systems <cli-cloud-client-add>` to the local cloud and
then :ref:`install it <cli-cloud-install>`!

``core_system_config/`` contains configuration files for the core systems, and ``docker-compose.yml`` is used
with the :ref:`startup command <cli-cloud-up>` to boot the core system docker containers.

.. warning::
   ``docker-compose.yml`` and the ``core_system_config/*.properties`` files should not be edited manually.

Lastly, the ``sql/`` directory is used by the database container, and this directory is set up by ``initSQL.sh``
during installation.

.. _cloud-configuration-file:

The Cloud Configuration File
----------------------------

To be written.