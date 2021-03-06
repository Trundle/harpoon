# encoding: utf-8

from __future__ import unicode_literals

import logging
from concurrent import futures
from functools import wraps

import click

from harpoon.docker import find_containers
from harpoon.hostlistproviders import ansible, hosts


class _EchoHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        click.echo(click.style(msg, fg="red"))


class _FireGroup(click.Group):
    """Custom group that wraps the commands that get added to it:
    - The command gets an extra argument "container_id"
    - The command's callback will return the pair (command return value, container id)
    """
    def add_command(self, cmd, name=None):
        click.argument("container_id")(cmd)
        cmd_callback = cmd.callback
        @wraps(cmd_callback)
        def callback(**kwargs):
            container_id = kwargs.pop("container_id")
            return (cmd_callback(**kwargs), container_id)
        cmd.callback = callback
        super(_FireGroup, self).add_command(cmd, name)


@click.group(cls=_FireGroup)
@click.option("-p", "--parallelism", default=5)
def fire(parallelism):
    root = logging.getLogger('')
    root.addHandler(_EchoHandler())
    root.setLevel(logging.WARN)


@fire.resultcallback()
def invoke(result, parallelism):
    (host_list, container_id) = result
    with futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
        containers = find_containers(executor, host_list, container_id)
    if containers:
        for container in containers:
            click.echo(click.style(container, fg="green"))
    else:
        msg = "Container {id} not found (hosts tried: {hosts})".format(
            id=container_id,
            hosts=", ".join(host_list))
        click.echo(click.style(msg, fg="red"), err=True)


ansible.create_provider_command(fire)
hosts.create_provider_command(fire)


if __name__ == "__main__":
    fire()
