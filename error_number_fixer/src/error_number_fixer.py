#!/bin/python
# coding=utf-8
import argparse
import difflib
import fnmatch
import logging
import ntpath
import os
import shutil
import sys
import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from lib2to3 import pygram
from lib2to3 import pytree
from lib2to3 import refactor
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Comma
from lib2to3.pgen2 import driver
from lib2to3.pytree import Leaf
from textwrap import dedent

logging.basicConfig()
logger = logging.getLogger("error_number_fixer")

PATTERN = """
    power< call='result' + trailer< '.' attr='error' > trailer< lpar='('
        ( not(arglist | argument<any '=' any>) arg_1=any
        | arglist< arg_1=any ',' arg_2=any > )
    rpar=')' > >
    |
    power< call='self' + trailer< '.' 'logger' > + trailer< '.' attr=('error' | 'user_error') > trailer< lpar='('
        ( not(arglist | argument<any '=' any>) arg_1=any
        | arglist< arg_1=any ',' arg_2=any > )
    rpar=')' > >
"""


class FixLoggerErrorNumber(BaseFix):
    BM_compatible = True
    keep_line_order = True
    order = "pre"

    def __init__(self, options, fixer_log, error_series):
        self.PATTERN = PATTERN
        self.count = error_series
        super(FixLoggerErrorNumber, self).__init__(options, fixer_log)

    def transform(self, node, results):
        self.count += 1
        if 'arg_2' in results:
            logger.debug("found 2 [%s %s]" %
                         (results['arg_1'], results['arg_2']))
            error_no = results['arg_1']
            error_no.replace(Leaf(type=2, value=self.count))
        else:
            logger.debug("found 1 [%s]" % results['arg_1'])
            siblings_list = results['arg_1'].parent.children
            siblings_list.insert(1, Leaf(type=2, value=self.count))
            siblings_list.insert(2, Comma())
            siblings_list[3].prefix = " "
        return node


class CodeFixers(refactor.MultiprocessRefactoringTool):

    def __init__(self, error_series, *args, **kwargs):
        self.error_series = int(error_series)
        super(CodeFixers, self).__init__(*args, **kwargs)

    def get_fixers(self):
        fixer = FixLoggerErrorNumber(
            self.options, self.fixer_log, self.error_series)
        return [fixer], []


def generate_fixed_code(source_code, error_series):
    flags = dict(print_function=True)
    code_fixer = CodeFixers(error_series, [], flags)
    refactored = code_fixer.refactor_string(dedent(source_code), 'script')
    return str(refactored)


def parse_code(file_path):
    parser_driver = driver.Driver(pygram.python_grammar, pytree.convert)
    parse_tree = parser_driver.parse_file(
        filename=file_path, encoding='ascii', debug=True)
    source_code = str(parse_tree)
    return source_code


def get_source_code(file_path):
    try:
        with open(file_path, 'r') as source_file:
            source_content = source_file.read()
            return source_content
    except Exception as exp:
        logger.error("Error in opening file")
        raise Exception(exp)


def write_to_file(file_path, modified_code, append_suffix):
    try:
        file_path = get_full_file_name(file_path, append_suffix)
        with open(file_path, 'w+') as target_file:
            target_file.write(modified_code)
    except Exception as exp:
        logger.error("Failed to write modified code to the file")
        raise Exception(exp)


def backup(file_path):
    backup_file = file_path + ".bak"
    if os.path.lexists(backup_file):
        try:
            os.remove(backup_file)
        except os.error:
            logger.error("Can't remove backup %s" % backup_file)
    try:
        shutil.copy(file_path, backup_file)
    except os.error:
        logger.error("Can't rename %s to %s" % (file_path, backup_file))


def get_full_file_name(file_path, append_suffix):
    head, tail = ntpath.split(file_path)
    tail = tail or ntpath.basename(head)
    if head:
        full_file_name = head + "/" + tail
    else:
        full_file_name = tail
    if append_suffix:
        file_parts = tail.split(".")
        file_name = file_parts[0] + "_" + append_suffix
        full_file_name = file_name + "." + file_parts[1]
    return full_file_name


def check_positive(value):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError(
            "%s is an invalid positive int value" % value)
    return int_value


def main(argv=None):
    """Command line options."""
    try:
        # Setup argument parser
        parser = ArgumentParser(description="FSO Plugin Error Number Fixer",
                                formatter_class=RawDescriptionHelpFormatter)

        # parser.add_argument("filepaths", help="The base directory for all input file(s)",
        #                     nargs='*')
        parser.add_argument('-i', "--input_directory", dest="input_dir",
                            help="The base directory for all input file(s). [default: %(default)s]",
                            metavar="file_path", required=True, nargs='+')
        parser.add_argument("-o", "--output_directory", dest="output_dir",
                            help="If supplied, all converted files will be written into "
                                 "this directory tree instead of input directory.",
                            metavar="output_path")
        parser.add_argument("-a", "--append_suffix", dest="append_suffix",
                            help="If supplied, all files output by this "
                                 "tool will have this appended to their filename.",
                            metavar="append_suffix")
        parser.add_argument('-e', "--error_series", dest="error_series",
                            help="Error series number", type=check_positive,
                            metavar="error_series")
        parser.add_argument("-w", "--write", dest="write", action="store_true",
                            help="Write the modified code to the source file",
                            default=True)
        parser.add_argument("-b", "--backup", dest="backup", action="store_true",
                            help="Backup file before refactoring",
                            default=False)
        parser.add_argument("-v", "--verbose", dest="verbose",
                            action="count", help="set verbosity level",
                            default=0)

        # Process arguments

        args = parser.parse_args(argv)
        input_args = args.input_dir
        output_dir = args.output_dir
        append_suffix = args.append_suffix
        write = args.write
        backup_file = args.backup
        error_series = args.error_series
        verbose = args.verbose

        if isinstance(verbose, int):
            if verbose > 0:
                logger.setLevel(logging.DEBUG)
                logger.debug("Verbose debug mode on")
            else:
                logger.setLevel(logging.INFO)

        logger.debug("Source Path: %s", input_args)
        logger.debug("Output Directory: %s", output_dir)
        logger.debug("verbosity level: %d", verbose)

        source_files = []
        for input_arg in input_args:
            if os.path.isfile(input_arg):
                source_files.append(input_arg)
            elif os.path.isdir(input_arg):
                for (dir_path, dir_names, file_names) in os.walk(input_arg):
                    for file_name in fnmatch.filter(file_names, '*.py'):
                        file_name = os.path.join(dir_path, file_name)
                        source_files.append(file_name)
            else:
                raise Exception(
                    "Invalid file or directory path specified.\nPlease verify if the path exists")

        if source_files:
            for source_file in source_files:

                # check backup
                if backup_file:
                    backup(source_file)

                source_code = get_source_code(source_file)

                # generate error series
                if not error_series:
                    file_name = os.path.basename(source_file).rstrip('.py')
                    ascii_sum = sum(ord(char) - 64 for char in file_name)
                    error_series = int(str(ascii_sum)[:3].ljust(5, '0'))

                modified_code = generate_fixed_code(source_code, error_series)

                # generate code diff
                diffed_lines = []
                for line in difflib.context_diff(
                        source_code.splitlines(),
                        modified_code.splitlines(),
                        fromfile='Before Fix',
                        tofile='After Fix',
                        n=0):
                    line = ' '.join(line.split()) + '\n'
                    diffed_lines.append(line)

                code_diff = "".join(diffed_lines)

                if code_diff:
                    print("\033[93mFixing error numbers: [%s]\033[0m" % source_file)
                    print(code_diff)
                    if write:
                        write_to_file(
                            source_file, modified_code, append_suffix)
                    elif output_dir:
                        write_to_file(output_dir, modified_code, append_suffix)
                    print("\n\033[93mPlease verify modified files and add files by running "
                          "`git add .` to approve modified files.\033[0m")

        else:
            logger.debug("No file found in the input directory")
            return 1

        return 0

    except (KeyboardInterrupt, SystemExit):
        return 2

    except Exception as exp:
        program_name = "error_number_fixer"
        tb = traceback.format_exc(exp)
        logger.debug('Caught Exception: %s', exp)
        sys.stderr.write('Caught exception {}'.format(tb))
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(exp) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 3


if __name__ == "__main__":
    exit(main())
