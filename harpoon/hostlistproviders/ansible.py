from __future__ import absolute_import

from getpass import getpass

import click
from ansible.parsing.dataloader import DataLoader
from ansible.inventory import Inventory
from ansible.vars import VariableManager


def _get_vault_password():
    return getpass("Vault password: ")


def create_provider_command(group):
    @group.command()
    @click.option("-i", "--inventory-file", default="/etc/ansible/hosts",
                  help="specify inventory host file")
    @click.option("--ask-vault-pass", is_flag=True, default=False,
                  help="ask for vault password")
    @click.option("--limit", default="all",
                  help="further limit selected hosts to an additional pattern")
    def ansible(ask_vault_pass, inventory_file, limit):
        loader = DataLoader()
        if ask_vault_pass:
            vault_pass = _get_vault_password()
            loader.set_vault_password(vault_pass)
        inventory = Inventory(loader, VariableManager(), host_list=inventory_file)
        hosts = inventory.get_hosts(limit)
        return [host.name for host in hosts]
    return ansible
