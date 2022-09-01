#!/usr/bin/env python3
# written by nathan sinclair

import sys
from argparse import ArgumentParser
from itertools import chain
from pathlib import Path

from bibtex_entry import BibTeXEntry, FormatError

#def set_citekey(file):


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-r', '--recursive', action='store_true'
                                         , help="recurse on each sub-directory")
    parser.add_argument('-y', '--type', action='store_true'
                                     , help="show the BibTeX type of each file")
    parser.add_argument('-ck', '--citekey', action='store_true'
                                         , help="show the citekey of each file")
    parser.add_argument('-t', '--tag', action='append'
                , metavar=('TAG'), help="show the content of TAG for each file")
    parser.add_argument('target', nargs='*', default=['.']
                                 , help="files with BibTeX entry to be printed")
    args = parser.parse_args()

    GLOB_PAT = '**/*.pdf' if args.recursive else '*.pdf'
    for filepath in chain.from_iterable(tp.glob(GLOB_PAT)
                                 if (tp := Path(targetname)).is_dir() else (tp,)
                                 for targetname in args.target):
        try:
            entry = BibTeXEntry.from_xattr(filepath)

            print(f"{filepath.name}:", file=sys.stderr)
            if entry is None:
                print('\tNo BibTeX entry attached to file', file=sys.stderr)
                continue

            if args.type:
                print(f"\ttype: {entry.type}")
            if args.citekey:
                print(f"\tciteKey: {entry.citekey}")
            if args.tag:
                for tag in args.tag:
                    if tag in vars(entry):
                        print(f'\t{tag} = {{{getattr(entry, tag)}}}')
                    else:
                        print(F"\t{tag}: NO SUCH TAG")

            if not (args.type or args.citekey or args.tag):
                print(entry)
            print(flush=True) # if &> file - this interleaves stdout and stderr

        except OSError as e:
            print(f"{e.filename}: {e.strerror}", file=sys.stderr)
            sys.exit(e.errno)
