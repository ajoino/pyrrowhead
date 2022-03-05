.. _howto-create-local-clouds:

Configuring Local Clouds
========================

The creation of local clouds consists of the three steps highlighted in :ref:`the tutorial <tutorial>`:
Creating the :ref:`cloud configuration <cli-cloud-create>`,
installing the :ref:`necessary files <cli-cloud-install>`,
and :ref:`starting the local cloud <cli-cloud-up>`.

Following these steps will create the smallest possible local cloud, one containing only the mandatory core systems.
But Pyrrowhead allows you to configure local clouds to contain more core and client systems.

Telling Pyrrowhead What Cloud To Use
------------------------------------

Since it is possible to have multiple local clouds configured at the same time, you need to tell Pyrrowhead what
cloud to apply your configuration to.
You do this the same way for all ``pyrrowhead cloud`` commands, by

* providing the CLOUD_IDENTIFIER argument,
* or setting the cloud and org names with the ``-c`` and ``-o`` options.

These options are mutually exclusive, you either provide a cloud identifier or use the name options.

.. note::
   The cloud and org names need to be `DNS-compliant <https://docs.rightscale.com/faq/clouds/aws/What_are_valid_S3_bucket_names.html>`_,
   which, for example, means the names cannot contain underscores.
   Pyrrowhead will tell you when a name is invalid but not why it is.

Examples
********

Valid commands:

.. code-block:: bash

   pyrrowhead cloud create example-cloud.example-org
   pyrrowhead cloud install -c example-cloud -o example-org

Invalid commands:

.. code-block:: bash

   pyrrowhead cloud up example-cloud.example-org -c test-cloud -o test-org

Core Systems
------------

Pyrrowhead includes the mandatory core systems by default.
Use the ``pyrrowhead cloud create --include <core_suite>`` option to add more.
The option takes the ``core-suite`` argument, which is currently one of three options:

* ``intercloud``
* ``eventhandler``
* ``onboarding``

Argument ``intercloud`` adds the gateway and gatekeeper systems to the local cloud, ``eventhandler`` adds the eventhandler,
and ``onboarding`` adds the system registry, device registry, onboarding controller, and certificate authority.
Pyrrowhead support for more core systems will be added later.
The ``--include`` option can be used multiple times to add as many of the available core suites as possible.

Client Systems
--------------

Client systems are added using the ``pyrrowhead client client-add`` command.
You are only required to use the ``--name/-n <SYSTEM_NAME>`` option, which takes the system name as an argument.
Like the cloud and org names, the system name needs to be DNS-compliant.

By only providing the system name, you let Pyrrowhead choose the ip-address and port of the system.
If you want to specify these options, use the ``--addr/-a`` option for the ip-address and ``--port/-p``
for the port.

Example use:

.. code-block:: bash

   pyrrowhead cloud client-add example-cloud.example-org -n example-system -a 127.0.0.1 -p 6000

IP-Network
----------

Pyrrowhead uses docker to run Arrowhead local clouds.
By default, Pyrrowhead will create a docker network on the 172.16.1.0/24 subnet, but you can specify other networks
by using the ``pyrrowhead cloud create --ip-network`` option.

.. note::
   It is not possible currently to specify the ip address of individual core systems.

.. note::
   It's up to you to make sure that local clouds' address space do not overlap if you try to run multiple local clouds.

Secure and Insecure Local Clouds
--------------------------------

Arrowhead local clouds can run in secure and insecure modes.
It is recommended to always run your local clouds in secure mode, and Pyrrowhead defaults to using secure mode.
However, it's useful sometimes to run local clouds in insecure mode, such as when you are testing new systems
that cannot run in secure mode yet.

Pyrrowhead allows you to specify secure mode with the ``pyrrowhead cloud create --enable-ssl`` command, and
insecure mode with the ``pyrrowhead cloud create --disable-ssl``.
