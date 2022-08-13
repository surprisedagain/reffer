#!/usr/bin/env python3
# written by nathan sinclair

from argparse import ArgumentParser
from itertools import chain
from pathlib import Path
from sys import stderr

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
    parser.add_argument('target', nargs='+', default=['.']
                                  , help="files with BibTeX extry to be edited")
    args = parser.parse_args()

    GLOB_PAT = '**/*.pdf' if args.recursive else '*.pdf'
    for filepath in chain.from_iterable(tp.glob(GLOB_PAT)
                                 if (tp := Path(targetname)).is_dir() else (tp,)
                                 for targetname in args.target):
        try:
            print(f'{filepath.name}:', file=stderr)
            entry = BibTeXEntry.from_xattr(filepath)

            if args.type:
                print(f"\t@{entry.type}")
            if args.citekey:
                print(f"\tCiteKey: {entry.citekey}")
            if args.tag:
                for tag in args.tag:
                    if tag in entry.tags:
                        print(f'\t{tag} = {{{entry.tags[tag]}}}')
                    else:
                        print(F"\t{tag}: NO SUCH TAG")

            if not (args.type or args.citekey or args.tag):
                print(entry)
            print(flush=True) # if &> file - this interleaves stdout and stderr
        except OSError as e:
            if e.errno == 93:
                print('No BibTeX entry attached to file')
            else:
                print(e.strerror)
