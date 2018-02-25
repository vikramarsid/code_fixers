# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import json
import logging

from utils.util import added_files
from utils.util import CalledProcessError
from utils.util import cmd_output

logging.basicConfig()
logger = logging.getLogger("check_added_plugin_files")

CHECK_FILES = {
    "_CHANGELOG.md": 0,
    ".tar": 0,
    ".pyc": 0
}

ERROR_DETAILS = {
    "_CHANGELOG.md": "\n [ X ] CHANGELOG.md file is missing. Please generate required file to commit changes.",
    ".tar": "\n [ X ] Plug-in package file is missing. Please generate plug-in package(.tar) to commit changes.",
    ".package": "\n [ X ] Plug-in package file is missing. Please generate plug-in package(.package) to commit changes."
}

NOT_ALLOWED_FILES = [".pyc"]


def warning(msg):
    print("\033[93m{}\033[0m".format(msg))


def error(msg):
    print("\033[91m{}\033[0m".format(msg))


def info(msg):
    print("\033[94m{}\033[0m".format(msg))


def lfs_files():
    try:
        # Introduced in git-lfs 2.2.0, first working in 2.2.1
        lfs_ret = cmd_output('git', 'lfs', 'status', '--json')
    except CalledProcessError:  # pragma: no cover (with git-lfs)
        lfs_ret = '{"files":{}}'

    return set(json.loads(lfs_ret)['files'])


def check_added_plugin_files(file_names):
    file_names = (added_files() & set(file_names)) - lfs_files()

    if not file_names:
        return 0

    return_value = 0
    for file_name in file_names:
        for check_file, count in CHECK_FILES.iteritems():
            if file_name.endswith(check_file):
                CHECK_FILES[check_file] = count + 1
                logger.debug("Found %s file" % file_name)
                continue

    for check_file_name, total_count in CHECK_FILES.iteritems():

        if total_count == 0:
            if check_file_name not in NOT_ALLOWED_FILES:
                print(ERROR_DETAILS[check_file_name])
                return_value += 1
        elif total_count > 1:
            if check_file_name in NOT_ALLOWED_FILES:
                warning("More than one *{} files are present. "
                        "Please delete all files with specified extension".format(check_file_name))
            else:
                error("More than one *{} files are present. Please delete extra files.".format(check_file_name))
            return_value += 1
        else:
            if check_file_name in NOT_ALLOWED_FILES:
                error("Please delete all *{} files".format(check_file_name))
                return_value += 1
            else:
                logger.debug("Checked %s file" % len(check_file_name))

    return return_value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        action="count",
        help="set verbosity level",
        default=0
    )
    args = parser.parse_args(argv)
    verbose = args.verbose
    file_names = args.filenames
    if isinstance(verbose, int):
        if verbose > 0:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose debug mode on")
        else:
            logger.setLevel(logging.INFO)

    logger.debug("Checking %s files" % len(file_names))
    if file_names:
        return_value = check_added_plugin_files(file_names)
        info("Please verify modified files and add files by running "
             "`git add .` to approve modified files.")
    else:
        logger.debug("No files available for checks.")
        return_value = 0

    return return_value


if __name__ == '__main__':
    exit(main())
