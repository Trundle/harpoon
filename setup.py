# encoding: utf-8

from setuptools import setup

from harpoon import __version__


setup(
    name="harpoon",
    author="Andreas Stührk",
    author_email="andy@hammerhartes.de",
    license="MIT",
    version=__version__,
    url="https://github.com/Trundle/harpoon",
    packages=["harpoon", "harpoon.bot", "harpoon.hostlistproviders",
              "harpoon.test"],
    entry_points={
        "console_scripts": [
            "harpoon = harpoon.__main__:fire",
            "harpoon-hipchat = harpoon.bot.hipchat:bot",
        ]
    },
    install_requires=[
        "ansible",
        "click",
        "docker-py",
        "futures",
        # Bot dependencies
        "sleekxmpp"
    ])
