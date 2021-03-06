from __future__ import absolute_import, division

import logging
import re
from functools import wraps
from itertools import chain
from textwrap import dedent

import docker
import requests
from requests.exceptions import HTTPError, RequestException


DOCKER_PORT = 2375
DOCKER_VERSION = "1.15"
TIMEOUT = 15


def _ignore_request_exception(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except RequestException as e:
            msg = "Error while contacting {}: {}".format(e.request.url, e)
            logging.warning(msg)
    return wrapper


def _is_no_such_container_exception(http_error):
    return (http_error.response.status_code == requests.codes.not_found
            and http_error.response.text.startswith("No such container: "))


@_ignore_request_exception
def _find_container_at_host(docker_client, container_id):
    try:
        info = docker_client.inspect_container(container_id)
    except HTTPError as exc:
        if not _is_no_such_container_exception(exc):
            raise
    else:
        return info


def _get_repo_tags(docker_client, image_id):
    # Unfortunately, there does not seem a better way :(
    for image in docker_client.images():
        if image["Id"] == image_id:
            return image["RepoTags"]


def _indent(lines, indentation):
    return indentation + ("\n" + indentation).join(lines.splitlines())


def _pretty_format_ports(ports):
    return "\n".join(
        "* {IP}:{PublicPort} -> {PrivatePort} ({Type})".format(**port)
        for port in ports if "IP" in port
    )


def _pretty_format_container(host, container, repo_tags):
    msg = dedent("""\
        Found container {id} on host {host}:
          - Tags: {tags}
          - Exposed ports: {ports}""")
    if container["Ports"]:
        ports = _pretty_format_ports(container["Ports"])
        ports = "\n" + _indent(ports, " " * 6)
    else:
        ports = "(none)"
    return msg.format(
        id=container["Id"][:12],
        host=host,
        tags=", ".join(repo_tags),
        ports=ports)


def _get_client(host):
    base_url = "tcp://{}:{}".format(host, DOCKER_PORT)
    return docker.Client(
        base_url=base_url,
        version=DOCKER_VERSION,
        timeout=TIMEOUT)


def _network_settings_to_ports(settings):
    for (port_and_type, ports) in settings["Ports"].items():
        if ports:
            (port, _, port_type) = port_and_type.partition("/")
            yield {
                "PrivatePort": int(port),
                "IP": ports[0]["HostIp"],
                "PublicPort": ports[0]["HostPort"],
                "Type": port_type,
            }


def find_container(executor, host_list, container_id):
    def query(host):
        docker_client = _get_client(host)
        container = _find_container_at_host(docker_client, container_id)
        return (host, docker_client, container)

    containers = filter(None, executor.map(query, host_list))
    for (host, docker_client, container) in containers:
        if container is not None:
            # "Unify" container model with that of find_containers_by_image
            ports = _network_settings_to_ports(container["NetworkSettings"])
            container["Ports"] = list(ports)

            repo_tags = _get_repo_tags(docker_client, container["Image"])
            return _pretty_format_container(host, container, repo_tags)


def _create_image_matcher(image):
    escaped_image = re.escape(image)
    without_registry_matcher = re.compile(escaped_image + "(:|$)").match
    with_registry_matcher = re.compile("/{}(:|$)".format(escaped_image)).search
    def matcher(s):
        return bool(without_registry_matcher(s) or with_registry_matcher(s))
    return matcher


def find_containers_by_image(executor, host_list, image):
    matcher = _create_image_matcher(image)

    @_ignore_request_exception
    def query(host):
        images = []
        docker_client = _get_client(host)
        for image in docker_client.images():
            if any(matcher(tag) for tag in image["RepoTags"]):
                images.append(image)

        containers_found = []
        if images:
            for container in docker_client.containers():
              for image in images:
                  if container["Image"] in image["RepoTags"]:
                      formatted_container = _pretty_format_container(
                          host, container, image["RepoTags"])
                      containers_found.append(formatted_container)

        return containers_found

    containers = filter(None, executor.map(query, host_list))
    return list(chain.from_iterable(containers))


def is_container_id(x):
    """Crude heuristic to decide whether the given string is a possible
    container ID.
    """
    digits = 0
    letters = 0
    for char in x:
        if '0' <= char <= '9':
            digits += 1
        elif 'a' <= char <= 'f':
            letters += 1
        else:
            return False
    return (digits / (letters + digits)) > 0.3


def find_containers(executor, host_list, image_or_container_id):
    if is_container_id(image_or_container_id):
        container = find_container(executor, host_list, image_or_container_id)
        return [container] if container else []
    else:
        return find_containers_by_image(
            executor, host_list, image_or_container_id)
