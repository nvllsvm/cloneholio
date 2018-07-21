cloneholio
==========
*I am cloneholio! I need backup for my Git host.*

|Version|

Maintain local backups of *all Git repositories* belonging to a user or group.

**Features:**

- Supports both GitHub and GitLab.
- Backup *all repositories* owned by users and groups.
- Scale to a configurable number of processes.


Installation
------------

.. code:: shell

    $ pip3 install cloneholio


Example
-------
This will backup all repositories owned by the `python`_ organziation on GitHub.

.. code:: bash

    $ cloneholio -t TOKEN -p github python
    INFO Begin "github" processing using "/home/draje/Code/GitLab/nvllsvm/cloneholio"
    INFO Processing python/asyncio
    INFO Processing python/bpo-builder
    ...
    INFO Processing python/typing
    INFO Finished "github" processing 62 repos with 0 failures



Help
----

.. code:: bash

    $ cloneholio -h
    usage: cloneholio [-h] [-n NUM_PROCESSES] [-d DIRECTORY] -t TOKEN
                      [-p {github,gitlab}]
                      paths [paths ...]

    Maintain local backups of all Git repositories belonging to a user or group.

    Token creation:
      - GitLab
        Permissions:  api
        URL:  https://gitlab.com/profile/personal_access_tokens

      - GitHub
        Permissions:  repo:status
        URL:  https://github.com/settings/tokens/new

    positional arguments:
      paths

    optional arguments:
      -h, --help            show this help message and exit
      -n NUM_PROCESSES      Number of processes to use
      -d DIRECTORY, --directory DIRECTORY
      -t TOKEN, --token TOKEN
      -p {github,gitlab}, --provider {github,gitlab}


.. |Version| image:: https://img.shields.io/pypi/v/cloneholio.svg?
   :target: https://pypi.org/project/cloneholio/

.. _python: https://github.com/python

