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

You can also provide a list of hosts manually instead of using
ansible: ``harpoon hosts host1.example.com host2.example.com
9b57c6457edc``.


Runnig the hipchat bot
======================

See https://www.hipchat.com/account/xmpp for your XMPP details.

``HIPCHAT_PASSWORD=geheim harpoon-hipchat --nickname "Your Name" --jid 1234_5678@chat.hipchat.com 1234_someroom@conf.hipchat.com ansible -i /path/to/your/inventory --ask-vault-pass``


License
=======

MIT/Expat. See ``LICENSE`` for details.
