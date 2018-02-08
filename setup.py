from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ansible-role-algosec",
    version="0.2.0",
    packages=["library"],
    url="https://github.com/AlmogCohen/ansible-role-algosec",
    license="MIT",
    author="Almog Cohen",
    description="Set of Ansible modules for Algosec services management",
    long_description=long_description,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        # "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
    ],
    install_requires=[
        "algosec~=0.6.0",
        "ansible",
    ],
)
