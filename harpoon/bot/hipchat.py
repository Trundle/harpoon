# encoding: utf-8

from __future__ import print_function, unicode_literals

import click
import logging
import re
from concurrent import futures

from sleekxmpp import ClientXMPP

from harpoon.docker import find_containers
from harpoon.hostlistproviders import ansible, hosts


MUC_EXTENSION = "xep_0045"
DELAY_EXTENSION = "xep_0203"


def _create_command_matcher():
    commands = {
        "harpoon",
        "-->",
        "\N{RIGHTWARDS HARPOON WITH BARB UPWARDS}",
        "\N{RIGHTWARDS HARPOON WITH BARB DOWNWARDS}",
    }
    alternatives = "|".join(map(re.escape, commands))
    return re.compile("({})(.+)$".format(alternatives)).match


class HarpoonBot(ClientXMPP):
    _HARPOON_COMMAND_MATCHER = _create_command_matcher()

    def __init__(self, jid, password, nick, rooms_to_join, executor,
                 host_list):
        ClientXMPP.__init__(self, jid, password)
        self._nick = nick
        self._rooms_to_join = rooms_to_join
        self._executor = executor
        self._host_list = host_list
        self.whitespace_keepalive = True
        self.whitespace_keepalive_interval = 60
        self.add_event_handler("session_start", self._on_session_started)
        self.add_event_handler("roster_update", self._on_roster_update)
        self.add_event_handler("message", self._on_message)
        self.register_plugin(DELAY_EXTENSION)
        self.register_plugin(MUC_EXTENSION)

    def _on_session_started(self, event):
        self.send_presence()
        self.get_roster()

    def _on_roster_update(self, event):
        for jid in self._rooms_to_join:
            self.plugin[MUC_EXTENSION].joinMUC(jid, self._nick, wait=True)

    def _on_message(self, message):
        body = message["body"].strip()
        if self._safe_to_react(message):
            match = self._HARPOON_COMMAND_MATCHER(body)
            if match:
                self._harpoon(message, match.group(2).strip())

    def _harpoon(self, message, container_id):
        containers = find_containers(
            self._executor, self._host_list, container_id)
        if containers:
            message.reply("\n\n".join(containers)).send()
        else:
            msg = "Container {id} not found (hosts tried: {hosts})".format(
                id=container_id,
                hosts=", ".join(self._host_list))
            message.reply(msg).send()

    def _safe_to_react(self, message):
        delayed = bool(message["delay"]["stamp"])
        from_me = message["from"].resource == self._nick
        return not delayed and not from_me


@click.group()
@click.option("-p", "--parallelism", default=5)
@click.option("--jid", envvar="HIPCHAT_JID")
@click.option("--password", envvar="HIPCHAT_PASSWORD")
@click.option("--nickname", envvar="HIPCHAT_NICKNAME")
@click.option("--room", multiple=True)
def bot(parallelism, jid, password, nickname, room):
    pass


@bot.resultcallback()
def run(host_list, parallelism, jid, password, nickname, room):
    logging.basicConfig(level=logging.WARN)

    with futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
        xmpp = HarpoonBot(jid, password, nickname, room, executor, host_list)
        xmpp.connect()
        xmpp.process(block=True)


ansible.create_provider_command(bot)
hosts.create_provider_command(bot)


if __name__ == "__main__":
    bot()
