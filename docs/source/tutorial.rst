.. _tutorial:

Pyrrowhead Quick-Start
======================

Pyrrowhead can be used to quickly create and manage local clouds.

There are :ref:`three options for installing Pyrrowhead <installation>`,
but the quickest is to just use ``pip`` normally:

.. code-block:: bash

   pip install pyrrowhead

Then, to create a new local cloud, run

.. code-block:: bash

   pyrrowhead cloud create test-cloud.test-org

This will create a new local cloud ``test-cloud`` under the organization ``test-org``, where the concatenation
``test-cloud.test-org`` is known as the cloud identifier.

Next, we will add a producer and a consumer to the cloud configuration.

.. code-block:: bash

   pyrrowhead cloud client-add test-cloud.test-org -n consumer
   pyrrowhead cloud client-add test-cloud.test-org -n provider

By adding these client systems to the cloud configuration we make sure that their
corresponding certificates are generated when the cloud is installed.
Speaking of installation, the cloud is installed (which means that the files
necessary to start the cloud are generated) with the command.

.. code-block:: bash

   pyrrowhead cloud install test-cloud.test-org

Now we can finally start the local cloud with

.. code-block:: bash

   pyrrowhead cloud up test-cloud.test-org

When the process ends you will have your local cloud up and running!

To confirm that pyrrowhead and the local cloud are running correctly, type

.. code-block:: bash

   pyrrowhead systems list

and check that the output looks like this (but hopefully more colorful!):

.. code-block:: console

                Registered systems

     id   System name        Address      Port
    ───────────────────────────────────────────
     2    orchestrator       172.16.1.4   8441
     3    authorization      172.16.1.5   8445
     5    service_registry   172.16.1.3   8443

If you got this far, congratulations! Pyrrowhead is working correctly for you.

Before you go on to read the :ref:`How-To guides <how-to>`, please remember to shut down the local cloud

.. code-block:: bash

   pyrrowhead cloud down test-cloud.test-org
