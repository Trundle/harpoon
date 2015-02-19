from __future__ import absolute_import

import logging

import docker
import requests
from requests.exceptions import HTTPError, RequestException

DOCKER_PORT = 2375
DOCKER_VERSION = "1.15"



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
    except RequestException as e:
        msg = "Error while contacting {}: {}".format(docker_client.base_url, e)
        logging.warning(msg)


def _get_repo_tags(docker_client, image_id):
    # Unfortunately, there does not seem a better way :(
    for image in docker_client.images():
        if image["Id"] == image_id:
            return image["RepoTags"]


def _pretty_format_container(host, container, repo_tags):
    return "Found container {id} on host {host.name} (tagged {tags})".format(
        id=container["Id"],
        host=host,
        tags=", ".join(repo_tags))


def find_container(host_list, container_id):
    for host in host_list:
        base_url = "tcp://{}:{}".format(host.name, DOCKER_PORT)
        docker_client = docker.Client(base_url=base_url, version=DOCKER_VERSION)
        container = _find_container(docker_client, container_id)
        if container is not None:
            repo_tags = _get_repo_tags(docker_client, container["Image"])
            return _pretty_format_container(host, container, repo_tags)
