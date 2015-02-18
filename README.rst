=======
harpoon
=======

Locates Docker containers with the help of an Ansible inventory.


Requirements
============

Python 2 (Ansible does not seem to support Python 3). Only tested with
Python 2.7.


Quickstart
==========

First, install harpoon: ``python setup.py install``.

Then, to find on which host container ``9b57c6457edc`` runs, use the
following command: ``harpoon ansible -i
/path/to/your/inventory --ask-vault-pass 9b57c6457edc``.


License
=======

MIT/Expat. See ``LICENSE`` for details.
