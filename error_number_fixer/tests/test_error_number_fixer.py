# coding=utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

from error_number_fixer.src.error_number_fixer import main
from utils.util import cmd_output

TEST_FILE_CONTENT = """
    self.logger.user_error("This is 1234")
    self.logger.error("This is 1234")
    result.error("This is 1234")
    result.error(234, "This is 234")
    result.error(456, "This is 456")
    """.rstrip() + '\n'


def test_nothing_added(temp_git_dir):
    with temp_git_dir.as_cwd():
        assert main([]) == 2


def test_adding_something(temp_git_dir):
    with temp_git_dir.as_cwd():
        test_files = []
        for test_file in range(3):
            test_file_name = str(test_file) + ".py"
            temp_git_dir.join(test_file_name).write(TEST_FILE_CONTENT)
            cmd_output('git', 'add', test_file_name)
            test_files.append(test_file_name)

        assert main(argv=['-i'] + test_files) == 0


def test_added_file_not_in_pre_commits_list(temp_git_dir):
    with temp_git_dir.as_cwd():
        temp_git_dir.join("1.py").write(TEST_FILE_CONTENT)
        cmd_output('git', 'add', "1.py")

        # File not present
        assert main(['-i', 'g.py']) == 3
