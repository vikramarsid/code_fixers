# coding=utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

import subprocess

import pytest

from check_added_plugin_files.src.check_added_plugin_files import check_added_plugin_files
from check_added_plugin_files.src.check_added_plugin_files import main
from utils.util import cmd_output

REQUIRED_FILES = ["TEST_CHANGELOG.md", "TEST.tar", "TEST.png", "TEST.package"]
NOT_ALLOWED_FILES = ["TEST.pyc"]


def test_nothing_added(temp_git_dir):
    with temp_git_dir.as_cwd():
        assert check_added_plugin_files(['f.py']) == 0


def test_adding_something(temp_git_dir):
    with temp_git_dir.as_cwd():
        for test_file in REQUIRED_FILES:
            temp_git_dir.join(test_file).write("print('hello world')")
            cmd_output('git', 'add', test_file)

        assert check_added_plugin_files(REQUIRED_FILES) == 0


def test_adding_not_allowed(temp_git_dir):
    with temp_git_dir.as_cwd():
        all_files = REQUIRED_FILES + NOT_ALLOWED_FILES
        for test_file in all_files:
            temp_git_dir.join(test_file).write("print('hello world')")
            cmd_output('git', 'add', test_file)

        assert check_added_plugin_files(all_files) >= 1


def test_added_file_not_in_pre_commits_list(temp_git_dir):
    with temp_git_dir.as_cwd():
        temp_git_dir.join(REQUIRED_FILES[0]).write("print('hello world')")
        cmd_output('git', 'add', REQUIRED_FILES[0])

        # Should pass even with a size of 0
        assert check_added_plugin_files(['g.py']) == 0


def test_integration(temp_git_dir):
    with temp_git_dir.as_cwd():
        assert main(argv=[]) == 0

        with temp_git_dir.as_cwd():
            for test_file in REQUIRED_FILES:
                temp_git_dir.join(test_file).write("print('hello world')")
                cmd_output('git', 'add', test_file)

        # Should not fail with default
        assert main(argv=REQUIRED_FILES) == 3


def has_gitlfs():
    output = cmd_output('git', 'lfs', retcode=None, stderr=subprocess.STDOUT)
    return 'git lfs status' in output


xfailif_no_gitlfs = pytest.mark.xfail(
    not has_gitlfs(), reason='This test requires git-lfs',
)


@xfailif_no_gitlfs
def test_allows_gitlfs(temp_git_dir):  # pragma: no cover
    with temp_git_dir.as_cwd():
        cmd_output('git', 'lfs', 'install')
        temp_git_dir.join('f.py').write('a' * 10000)
        cmd_output('git', 'lfs', 'track', 'f.py')
        cmd_output('git', 'add', '--', '.')
        # Should succeed
        assert main(('f.py',)) == 0


@xfailif_no_gitlfs
def test_moves_with_gitlfs(temp_git_dir):  # pragma: no cover
    with temp_git_dir.as_cwd():
        cmd_output('git', 'lfs', 'install')
        cmd_output('git', 'lfs', 'track', 'a.tar', 'b.tar')
        # First add the file we're going to move
        temp_git_dir.join('a.tar').write('a' * 10000)
        cmd_output('git', 'add', '--', '.')
        cmd_output('git', 'commit', '--no-gpg-sign', '-am', 'foo')
        # Now move it and make sure the hook still succeeds
        cmd_output('git', 'mv', 'a.tar', 'b.tar')
        assert main(('b.tar',)) == 0
