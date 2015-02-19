# encoding: utf-8

from __future__ import print_function, unicode_literals

import click
import logging

from sleekxmpp import ClientXMPP

from harpoon.docker import find_container
from harpoon.hostlistproviders import ansible


MUC_EXTENSION = "xep_0045"
DELAY_EXTENSION = "xep_0203"


class HarpoonBot(ClientXMPP):
    def __init__(self, jid, password, rooms_to_join, host_list):
        ClientXMPP.__init__(self, jid, password)
        self._rooms_to_join = rooms_to_join
        self._host_list = host_list
        self.add_event_handler("session_start", self._on_session_started)
        self.add_event_handler("roster_update", self._on_roster_update)
        self.add_event_handler("message", self._on_message)
        self.register_plugin(DELAY_EXTENSION)
        self.register_plugin(MUC_EXTENSION)

    def _on_session_started(self, event):
        self.send_presence()
        self.get_roster()

    def _on_roster_update(self, event):
        for (jid, nick) in self._rooms_to_join:
            self.plugin[MUC_EXTENSION].joinMUC(jid, nick, wait=True)

    def _on_message(self, message):
        delayed = bool(message["delay"]["stamp"])
        body = message["body"]
        if message["type"] == "groupchat" and not delayed and "harpoon" in body:
            container_id = body.split(None, 1)[-1]
            container = find_container(self._host_list, container_id)
            if container:
                msg = container
            else:
                msg = "Container {id} not found (hosts tried: {hosts})".format(
                    id=container_id,
                    hosts=", ".join(host.name for host in self._host_list))
            message.reply(msg).send()


@click.group()
@click.option("--jid", envvar="HIPCHAT_JID")
@click.option("--password", envvar="HIPCHAT_PASSWORD")
@click.option("--nickname", envvar="HIPCHAT_NICKNAME")
@click.argument("room")
def bot(jid, password, nickname, room):
    pass


@bot.resultcallback()
def run(host_list, jid, password, nickname, room):
    logging.basicConfig(level=logging.WARN)

    xmpp = HarpoonBot(jid, password, [(room, nickname)], host_list)
    xmpp.connect()
    xmpp.process(block=True)


ansible.create_provider_command(bot)


if __name__ == "__main__":
    bot()
