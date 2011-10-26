.. include:: ../README.rst

Installation
------------

::

    pip install fabric-provision

Usage
-----
- Create a ``fabfile.py``

::

    from fabric.api import *
    from provision import chef, provision

    env.hosts = ['vagrant@localhost:2222']

    chef.add_recipe('python')

- Assuming you have a `Vagrant <http://vagrantup.com/>`_ machine running locally,
  you can provision it instantly:

::

    $ fab provision

What it does
------------

- ``apt-get update``
- ``apt-get upgrade``
- Install a current version of `Chef <http://www.opscode.com/chef/>`_
- Run your configured recipes

API
---

.. currentmodule:: provision.chef

.. function:: add_recipe(recipe)

    Adds a recipe to run when provisioning. Alternatively you can just
    override ``provision.chef.recipes``.

Settings
--------

.. currentmodule:: provision.chef

.. attribute:: path

    :default: ``'/var/chef'``

    Remote path to store cookbooks and cached files.

.. attribute:: cookbooks

    :default: ``'cookbooks/'``

    The local path to your recipes, relative to you ``fabfile.py``.

.. attribute:: log_level

    :default: ``'info'``

    Chef's log level.

.. attribute:: gems

    :default: ``'1.8.10'``

    Which version of ``gem`` to install.


.. attribute:: recipes

    :default: ``[]``

    The list of recipes to run.

.. attribute:: json

    :default: ``{}``

    Additional JSON information you'd like to transfer to the server.