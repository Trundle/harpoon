# encoding: utf-8

from __future__ import unicode_literals

import logging

import click

from harpoon.docker import find_container
from harpoon.hostlistproviders import ansible


class _EchoHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        click.echo(click.style(msg, fg="red"))


class _FireGroup(click.Group):
    def add_command(self, cmd, name=None):
        click.argument("container_id")(cmd)
        cmd_callback = cmd.callback
        def callback(**kwargs):
            container_id = kwargs.pop("container_id")
            return (cmd_callback(**kwargs), container_id)
        cmd.callback = callback
        super(_FireGroup, self).add_command(cmd, name)


@click.group(cls=_FireGroup)
def fire():
    root = logging.getLogger('')
    root.addHandler(_EchoHandler())
    root.setLevel(logging.WARN)


@fire.resultcallback()
def invoke(result):
    (host_list, container_id) = result
    container = find_container(host_list, container_id)
    if container:
        click.echo(click.style(container, fg="green"))
    else:
        msg = "Container {id} not found (hosts tried: {hosts})".format(
            id=container_id,
            hosts=", ".join(host.name for host in host_list))
        click.echo(click.style(msg, fg="red"), err=True)


ansible.create_provider_command(fire)


if __name__ == "__main__":
    fire()
