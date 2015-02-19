# encoding: utf-8

from __future__ import unicode_literals

from getpass import getpass

import click
import docker
import requests
from ansible.inventory import Inventory
from requests.exceptions import HTTPError, RequestException


DOCKER_PORT = 2375
DOCKER_VERSION = "1.15"


def _get_vault_password(ask_for_password):
    if ask_for_password:
        return getpass("Vault password: ")


def _is_no_such_container_exception(http_error):
    return (http_error.response.status_code == requests.codes.not_found
            and http_error.response.text.startswith("No such container: "))


def _find_container(docker_client, container_id):
    try:
        try:
            info = docker_client.inspect_container(container_id)
        except HTTPError as exc:
            if not _is_no_such_container_exception(exc):
                raise
        else:
            return info
    except RequestException as exc:
        msg = "Error while contacting {}: {}".format(docker_client.base_url,
                                                     exc)
        click.echo(click.style(msg, fg="red"), err=True)


def _get_repo_tags(docker_client, image_id):
    # Unfortunately, there does not seem a better way :(
    for image in docker_client.images():
        if image["Id"] == image_id:
            return image["RepoTags"]


def _pretty_print_container(host, container, repo_tags):
    msg = "Found container {id} on host {host.name} (tagged {tags})".format(
        id=container["Id"],
        host=host,
        tags=", ".join(repo_tags))
    click.echo(click.style(msg, fg="green"))


@click.group()
def fire():
    pass


@fire.command()
@click.option("-i", "--inventory-file")
@click.option("--ask-vault-pass", is_flag=True, default=False)
@click.option("--limit", default="all")
@click.argument("container_id")
def ansible(ask_vault_pass, inventory_file, limit, container_id):
    vault_pass = _get_vault_password(ask_vault_pass)
    inventory = Inventory(inventory_file, vault_password=vault_pass)
    host_list = inventory.get_hosts(limit)
    for host in host_list:
        base_url = "tcp://{}:{}".format(host.name, DOCKER_PORT)
        docker_client = docker.Client(base_url=base_url, version=DOCKER_VERSION)
        container = _find_container(docker_client, container_id)
        if container is not None:
            repo_tags = _get_repo_tags(docker_client, container["Image"])
            _pretty_print_container(host, container, repo_tags)
            break
    else:
        msg = "Container {id} not found (hosts tried: {hosts})".format(
            id=container_id,
            hosts=", ".join(host.name for host in host_list))
        click.echo(click.style(msg, fg="red"), err=True)


if __name__ == "__main__":
    fire()
