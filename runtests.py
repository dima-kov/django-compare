#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line


def main(argv=None):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'compare.tests.settings'
    argv = argv or []
    execute_from_command_line(argv)


if __name__ == '__main__':
    sys.exit(bool(main(sys.argv)))
