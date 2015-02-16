#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2015
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Common code
"""
from contextlib import closing
from email.mime.text import MIMEText
import logging
import multiprocessing
from os.path import join, dirname, basename, expanduser
import re
import tarfile
import unicodedata
import time

from fabric.api import settings, cd, sudo, run
from fabric.utils import fastprint, puts
import sys

from settings_file import USERNAME, AWS_KEY, PIP_PACKAGES


def get_logger(level=multiprocessing.SUBDEBUG):
    logger = multiprocessing.get_logger()
    formatter = logging.Formatter('[%(processName)s]:%(asctime)-15s:%(levelname)s:%(module)s:%(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = 0

    if level:
        logger.setLevel(level)

    return logger


LOGGER = get_logger()


class Consumer(multiprocessing.Process):
    """
    A class to process jobs from the queue
    """
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self._queue = queue

    def run(self):
        """
        Sit in a loop
        """
        while True:
            LOGGER.info('Getting a task')
            next_task = self._queue.get()
            if next_task is None:
                # Poison pill means shutdown
                LOGGER.info('Exiting')
                self._queue.task_done()
                return
            LOGGER.info('Executing the task')
            next_task()
            self._queue.task_done()


def make_safe_filename(name):
    if isinstance(name, unicode):
        name = unicodedata.normalize('NFKD', name)
        name = name.encode('ascii', 'ignore').lower()
    else:
        name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '-', name).strip('-')
    name = re.sub(r'[-]+', '-', name)

    return name


def get_boto_data():
    dot_boto = join(expanduser('~'), '.boto')
    with open(dot_boto, 'r') as my_file:
        data = my_file.read()

    return data


def get_script(file_name):
    """
    Get the script from the bash directory
    """
    here = dirname(__file__)
    bash = join(here, '../bash', file_name)
    with open(bash, 'r') as my_file:
        data = my_file.read()

    return data


def get_cloud_init():
    return MIMEText('''
#cloud-config
repo_update: true
repo_upgrade: all

# Install additional packages on first boot
packages:
 - wget
 - git
 - python-pip
 - libXrandr
 - libXfixes
 - libXcursor
 - libXinerama

# Log all cloud-init process output (info & errors) to a logfile
output : { all : ">> /var/log/chiles-output.log" }

# Final_message written to log when cloud-init processes are finished
final_message: "System boot (via cloud-init) is COMPLETE, after $UPTIME seconds. Finished at $TIMESTAMP"
''')


def setup_aws_machine(hostname):
    LOGGER.info('Waiting for the ssh daemon to start up')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')
    with settings(user=USERNAME, key_filename=AWS_KEY, host_string=hostname, connection_attempts=5, timeout=30):
        with cd('/home/ec2-user/chiles_pipeline'):
            run('git pull')
        sudo('pip install {0}'.format(PIP_PACKAGES))
        run('''echo "{0}
" > /home/ec2-user/.boto'''.format(get_boto_data()))


def make_tarfile(output_filename, source_dir):
    LOGGER.info('output_filename: {0}, source_dir: {1}'.format(output_filename, source_dir))
    with closing(tarfile.open(output_filename, "w:gz")) as tar:
        tar.add(source_dir, arcname=basename(source_dir))


def format_arg_value(arg_val):
    """ Return a string representing a (name, value) pair.

    >>> format_arg_value(('x', (1, 2, 3)))
    'x=(1, 2, 3)'
    """
    arg, val = arg_val
    return "%s=%r" % (arg, val)


def echo(fn, write=sys.stdout.write):
    """ Echo calls to a function.

    Returns a decorated version of the input function which "echoes" calls
    made to it by writing out the function's name and the arguments it was
    called with.
    """
    import functools
    # Unpack function's arg count, arg names, arg defaults
    code = fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
    fn_defaults = fn.func_defaults or list()
    argdefs = dict(zip(argnames[-len(fn_defaults):], fn_defaults))

    @functools.wraps(fn)
    def wrapped(*v, **k):
        # Collect function arguments by chaining together positional,
        # defaulted, extra positional and keyword arguments.
        positional = map(format_arg_value, zip(argnames, v))
        defaulted = [format_arg_value((a, argdefs[a]))
                     for a in argnames[len(v):] if a not in k]
        nameless = map(repr, v[argcount:])
        keyword = map(format_arg_value, k.items())
        args = positional + defaulted + nameless + keyword
        write("%s(%s)\n" % (name(fn), ", ".join(args)))
        return fn(*v, **k)
    return wrapped
