# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import signal

import pytest

from utils.util import cmd_output

GIT_DIR = None


def clean_up():
    dir_path = os.path.abspath(GIT_DIR.dirname + "/..")
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def temp_git_dir(tmpdir):
    global GIT_DIR
    GIT_DIR = tmpdir.join('gits')
    cmd_output('git', 'init', '--', GIT_DIR.strpath)
    try:
        yield GIT_DIR
    finally:
        clean_up()


signal.signal(signal.SIGTERM, clean_up)
