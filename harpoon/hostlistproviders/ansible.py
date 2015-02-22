from __future__ import absolute_import

from getpass import getpass

import click
from ansible.inventory import Inventory


def _get_vault_password(ask_for_password):
    if ask_for_password:
        return getpass("Vault password: ")


def create_provider_command(group):
    @group.command()
    @click.option("-i", "--inventory-file")
    @click.option("--ask-vault-pass", is_flag=True, default=False)
    @click.option("--limit", default="all")
    def ansible(ask_vault_pass, inventory_file, limit):
        vault_pass = _get_vault_password(ask_vault_pass)
        inventory = Inventory(inventory_file, vault_password=vault_pass)
        hosts = inventory.get_hosts(limit)
        return [host.name for host in hosts]
    return ansible
