#!/usr/bin/env python3
# written by nathan sinclair

import os, tempfile, errno
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from time import sleep

from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--multiple', action='store_true', help="read a sequence of BibTeX entries from target and inject them into the files specified in their file tags.")
    group.add_argument('bibtexfile', nargs='?', help="file containing BibTeX entry to be injected")
    parser.add_argument('target', help="file to be injected with BibTeX extry")
    args = parser.parse_args()

    try:
        if args.multiple: # read multiple bibtex entries from args.target
            for bib in BibTeXEntry.read_entries(open(args.target, 'r').read()):
                try:
                    filepath = Path(bib.file).resolve()
                    del bib.file
                    bib.inject(filepath)
                    print(f'BibTeX Entry set for "{bib.file}"')

                except (FileNotFoundError, PermissionError, IOError) as e:
                    print(f"WARNING: {e.strerror}: '{e.filename.decode()}'\n"
                                              "Entry skipped.", file=sys.stderr)
                except KeyError as e:
                    print(f"WARNING: Entry for '{bib.title}' does not "
                          "have a 'file' tag.\nEntry skipped.", file=sys.stderr)
        else:
            if args.bibtexfile: # entry in bibtexfile
                bib = BibTeXEntry.from_str(open(args.bibtexfile, 'r').read())
            else: # entry to be hand written by user from template
                if not (fp_ := Path(args.target).resolve()).exists():
                    raise FileNotFoundError(errno.ENOENT, "File not found"
                                                                     , str(fp_))
                EDITOR = os.environ.get('EDITOR', 'nano')
                tf = tempfile.NamedTemporaryFile(suffix='.tmp', delete=False)
                tf.write(BibTeXEntry.ENTRY_TEMPLATE.encode())
                tf.close()
                try:
                    while True:
                        try:
                            run([EDITOR, tf.name])
                            tf = open(tf.name, 'r')
                            bib = BibTeXEntry.from_str(tf.read())
                        except FormatError as e:
                            print('WARNING: Could not recognise entry format: '
                               f'Last read char {e.args[0]} in file "{tf.name}"'
                               , file=sys.stderr)
                            sleep(4)
                            continue
                        else:
                            break
                        finally:
                            tf.close()
                finally:
                    os.remove(tf.name)

            bib.inject(args.target)
            print(f'Entry set for "{args.target}"')

    except OSError as e:
        if isinstance(e.filename, bytes):
            e.filename = e.filename.decode()
        print(f"ERROR: {e.strerror}: '{e.filename}'", file=sys.stderr)
        sys.exit(e.errno)
