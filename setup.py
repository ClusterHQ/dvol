from setuptools import setup

setup(
    name="dvol",
    packages=[
        "dvol",
    ],
    entry_points={
        "console_scripts": [
            "dvol = voluminous.dvol:main",
            "dvol-docker-plugin = voluminous.plugin:main",
        ],
    },
    version="0.1",
    description="A docker volume manager with git-like functionality.",
    author="Luke Marsden",
    author_email="luke@clusterhq.com",
    url="https://github.com/ClusterHQ/dvol",
    install_requires=[
        #"PyYAML>=3",
        "Twisted>=14.0.2",
        "treq>=14",
        "pyasn1>=0.1",
        "docker-py>=1.5.0",
    ],
)
