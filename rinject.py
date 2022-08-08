#!/usr/bin/env python3
# written by nathan sinclair
import argparse, os, tempfile
from subprocess import run
from sys import stderr
from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--multiple', action='store_true', help="read a sequence of BibTeX entries from target and inject them into the files specified in their file tags.")
    group.add_argument('bibtexfile', nargs='?', help="file containing BibTeX entry to be injected")
    parser.add_argument('target', help="file to be injected with BibTeX extry")
    args = parser.parse_args()

    try:
        if args.multiple:
            with open(args.target, 'r') as bibfile:
                for entry in BibTeXEntry.read_entries(bibfile.read()):
                    try:
                        entry.inject(filename := entry.tags.pop('file'))
                        print(f'BibTeX Entry set for "{filename}"')
                    except (FileNotFoundError, PermissionError) as e:
                        print('WARNING: Could not access file '
                               f'"{e.filename.decode()}": {e.strerror}\n'
                               'Entry skipped.', file=stderr)
                    except KeyError as e:
                        print(f'WARNING: Entry for "{entry.tags["title"]}" does'
                            'not have a file tag.\nEntry skipped.', file=stderr)
        else:
            if args.bibtexfile: # entry in bibtexfile
                with open(args.bibtexfile, 'r') as bibfile:
                    entry = BibTeXEntry.from_str(bibfile.read())
            else: # entry to be hand written by user from template
                EDITOR = os.environ.get('EDITOR', 'nano')
                tf = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False)
                tf.write(BibTeXEntry.ENTRY_TEMPLATE.encode())
                tf.close()
                while True:
                    try:
                        run([EDITOR, tf.name])
                        tf = open(tf.name, 'r')
                        entry = BibTeXEntry.from_str(tf.read())
                    except FormatError as e:
                        print('WARNING: Could not recognise entry format: '
                               f'Last read char {e.args[0]} in file "{tf.name}"'
                               , file=stderr)
                        continue
                    else:
                        break
                    finally:
                        tf.close()
                os.remove(tf.name)

            entry.inject(args.target)
            print(f'Entry set for "{args.target}"')

    except (FileNotFoundError, PermissionError) as e:
        # this clumsyness forced by xattr using b'filename' when raising errors
        if isinstance(e.filename, bytes):
            e.filename = e.filename.decode()
        print(f'WARNING: Could not access file "{e.filename}": {e.strerror}'
                                                                  , file=stderr)
