#!/usr/bin/env python3
# written by nathan sinclair

import os, sys, readline, errno
import subprocess, tempfile

from argparse import ArgumentParser
from itertools import chain
from pathlib import Path
from time import sleep

from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--citekey'
                               , help="set the citekey of the entry to CITEKEY")
    group.add_argument('-ac', '--autocitekey',  action='store_true'
                                      , help="autoset the citekey of the entry")

    parser.add_argument('-t', '--tag', nargs=2, action='append'
              , metavar=('TAG','VALUE'), help="set the content of TAG to VALUE")
    parser.add_argument('-te', '--tagedit', action='append', metavar=('TAGNAME')
                             , help='interactively edit the content of TAGNAME')
    parser.add_argument('-ta', '--tagappend', nargs=2, action='append'
                                   , metavar=('TAG', "ADDENDUM")
                                   , help="append ADDENDUM to the value of TAG")

    parser.add_argument('target', nargs='+'
                                , help="file(s) with BibTeX entry to be edited")
    args = parser.parse_args()

    for filepath in (Path(targetname).resolve() for targetname in args.target):
        try:
            if filepath.is_dir():
                raise IsADirectoryError(errno.EISDIR, "Is a directory"
                                                                , str(filepath))

            bib = BibTeXEntry.from_xattr(filepath)

            if not (args.citekey or args.autocitekey or args.tag or args.tagedit
                                                             or args.tagappend):
                EDITOR = os.environ.get('EDITOR', 'nano')
                tf = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False)
                if bib:
                    tf.write(str(bib).encode())
                else:
                    tf.write(BibTeXEntry.ENTRY_TEMPLATE.encode())
                tf.close()
                try:
                    while True: # repeat until no errors raised
                        try:
                            subprocess.run([EDITOR, tf.name])
                            tf = open(tf.name, 'r')
                            bib = BibTeXEntry.from_str(tf.read())
                        except FormatError as e:
                            print('WARNING: Could not recognise entry format: '
                                 f'Last read char {e.args[0]}', file=sys.stderr)
                            sleep(4)
                            continue
                        else:
                            break
                        finally:
                            tf.close()
                finally:
                    os.remove(tf.name)

            elif bib is None:
                print(f'{filepath}:\n\tNo BibTeX entry attached to file'
                                                              , file=sys.stderr)
                continue

            print(f"{filepath.name}:", file=sys.stderr)
            # various ways to modify bib based on command option
            if args.citekey:
                bib.citekey = args.citekey

            elif args.autocitekey:
                bib.autoset_citekey()

            if args.tag:
                for key, value in args.tag:
                    setattr(bib, key, value)

            if args.tagappend:
                for key, suffix in args.tagappend:
                    old_value = getattr(bib, key, '')
                    setattr(bib, key, old_value+suffix)

            if args.tagedit:
                try:
                    for key in args.tagedit:
                        default = getattr(bib, key, '')
                        readline.set_startup_hook(lambda: readline.insert_text(default))
                        new_value = input(f"\tSet '{key}' to: ")
                        if new_value:
                            setattr(bib, key, new_value)
                        elif hasattr(bib, key):
                            delattr(bib, key)
                finally:
                    readline.set_startup_hook()

            bib.inject(filepath)
            print(f'\tBibTeX entry for "{filepath}" updated')

        except FileNotFoundError as e:
            print(f"ERROR: {e.strerror}: {e.filename}", file=sys.stderr)
            sys.exit(e.errno)
        except IsADirectoryError as e:
            print(f"ERROR: {e.strerror}: {e.filename}", file=sys.stderr)
            sys.exit(e.errno)
