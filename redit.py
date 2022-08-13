#!/usr/bin/env python3
# written by nathan sinclair
import os, re, readline, sys, tempfile
from argparse import ArgumentParser
from subprocess import run
from time import sleep

from bibtex_entry import BibTeXEntry, FormatError

#def set_citekey(file):


if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-ck', '--citekey'
                               , help="set the citekey of the entry to CITEKEY")
    group.add_argument('-ak', '--autocitekey',  action='store_true'
                                      , help="autoset the citekey of the entry")
    parser.add_argument('-t', '--tag', nargs=2, action='append'
              , metavar=('TAG','VALUE'), help="set the content of TAG to VALUE")
    parser.add_argument('-te', '--tagedit', action='append'
         , metavar=('TAGNAME'), help='interactively set the content of TAGNAME')
    parser.add_argument('target', help="file with BibTeX extry to be edited")
    args = parser.parse_args()

    # get the entry to be edited
    try:
        entry = BibTeXEntry.from_xattr(args.target)
    except OSError as e:
        # this decode required because xattr uses b'filename'
        if isinstance(e.filename, bytes):
            e.filename = e.filename.decode()
        sys.exit(e)

    # various ways to modify entry based on command option
    if args.citekey:
        entry.citekey = args.citekey

    elif args.autocitekey:
        entry.autoset_citekey()

    if args.tag:
        for key, value in args.tag:
            entry.tags[key] = value

    if args.tagedit:
        try:
            for key in args.tagedit:
                default = entry.tags.get(key, '')
                readline.set_startup_hook(lambda: readline.insert_text(default))
                new_value = input(f"Set '{key}' to: ")
                if new_value:
                    entry.tags[key] = new_value
                else:
                    del entry.tags[key]
        finally:
            readline.set_startup_hook()

    if not (args.citekey or args.autocitekey or args.tag or args.tagedit):
        EDITOR = os.environ.get('EDITOR', 'nano')
        tf = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False)
        tf.write(entry.__str__().encode())
        tf.close()
        try:
            while True:
                try:
                    run([EDITOR, tf.name])
                    tf = open(tf.name, 'r')
                    entry = BibTeXEntry.from_str(tf.read())
                except FormatError as e:
                    print('WARNING: Could not recognise entry format: Last read '
                           f'char {e.args[0]}', file=sys.stderr)
                    sleep(4)
                    continue
                else:
                    break
                finally:
                    tf.close()
        finally:
            os.remove(tf.name)

    entry.inject(args.target)
    print(f'BibTeX entry for "{args.target}" updated')
