#!/usr/bin/env python3
# written by nathan sinclair
import argparse, os, tempfile, re
from subprocess import run
from sys import stderr

from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-ck', '--citekey', help="set the citekey of the entry to CITEKEY")
    group.add_argument('-ak', '--autocitekey',  action='store_true', help="autoset the citekey of the entry")
    parser.add_argument('-t', '--tag', nargs=2, metavar=('TAG','VALUE'), help="set the content of TAG to VALUE")
    parser.add_argument('target', help="file with BibTeX extry to be edited")
    args = parser.parse_args()

    # get the entry to be edited
    entry = BibTeXEntry.from_xattr(args.target)

    # various ways to modify entry based on command option
    if args.citekey:
        entry.citekey = args.citekey
    elif args.autocitekey:
        if 'author' in entry.tags:
            name = re.match(r'\s*(?P<name>\w+)', entry.tags['author']).group(
                                                                         'name')
        else:
            name = ''
        year = entry.tags.get('year', '') # string expected
        entry.citekey = name + year
    elif args.tag:
        entry.tags[args.tag[0]] = args.tag[1]
    else: # open editor to edit BibTeX entry
        EDITOR = os.environ.get('EDITOR', 'nano')
        tf = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False)
        tf.write(entry.__str__().encode('utf-8'))
        tf.close()
        while True:
            try:
                run([EDITOR, tf.name])
                tf = open(tf.name, 'r')
                entry = BibTeXEntry.from_str(tf.read())
            except FormatError as e:
                print('WARNING: Could not recognise entry format: Last read '
                           f'char {e.args[0]} in file "{tf.name}"', file=stderr)
                continue
            else:
                break
            finally:
                tf.close()
        os.remove(tf.name)

    entry.inject(args.target)
    print(f'New BibTeX entry for "{args.target}" written')

'''except (FileNotFoundError, PermissionError) as e:
        # this clumsyness forced by xattr using b'filename' when raising errors
        if isinstance(e.filename, bytes):
            e.filename = e.filename.decode()
        print(f'WARNING: Could not access file "{e.filename}": {e.strerror}'
                                                                  , file=stderr)
'''
