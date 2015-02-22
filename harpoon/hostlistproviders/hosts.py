import click


def create_provider_command(group):
    @group.command()
    @click.argument("hosts", nargs=-1)
    def hosts(hosts):
        return hosts
