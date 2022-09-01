#!/usr/bin/env python3
# written by nathan sinclair

from argparse import ArgumentParser
from itertools import chain
from pathlib import Path

import subprocess
import re
import sys

from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-r', '--recursive', action='store_true'
                                         , help="recurse on each sub-directory")
    parser.add_argument('-a', '--all', action='store_true'
                            , help="search for conjunction of all search terms")
    parser.add_argument('-ck', '--citekey', metavar=('CITEKEY')
                                                    , help="search for CITEKEY")
    parser.add_argument('-k', '--keyword', action='append', metavar=('TERM')
                                      , help="search for TERM in keywords tags")
    parser.add_argument('-t', '--tag', nargs=2, action='append'
                          , metavar=('TAG','VALUE')
                          , help="search for VALUE in TAG in each BibTeX entry")
    parser.add_argument('-n', '--note', action='append', metavar=('TERM')
                                        , help="search for TERM in annotations")
    parser.add_argument('target', nargs='*', default=['.']
                          , help="Directory or file whose BibTeX entry and skim"
                                               "annotations are to be searched")
    args = parser.parse_args()

    GLOB_PAT = '**/*.pdf' if args.recursive else '*.pdf'
    for filepath in chain.from_iterable(tp_.glob(GLOB_PAT)
                               if (tp_ := Path(targetname)).is_dir() else (tp_,)
                               for targetname in args.target):
        try:
            bib = BibTeXEntry.from_xattr(filepath)
            if bib is None:
                print(f"{filepath}:\n\tNo Bibtex entry attached to file"
                                                                  , file=sys.stderr)

            result = ""
            if args.citekey and args.citekey in bib.citekey:
                result += f"\tcitekey: {bib.citekey}\n"

            if args.keyword and any(search_term in getattr(bib, 'keywords', '')
                                               for search_term in args.keyword):
                result += f"\tkeywords = {{{bib.keywords}}}\n"

            if args.tag:
                tmp_result = set()
                for search_tag, search_term in args.tag:
                    if search_term in getattr(bib, search_tag, ''):
                        tmp_result.add(
                            "\t{search_tag} = {{{getattr(bib, search_tag)}}}\n")
                result += "".join(tmp_result)

            if args.note:
                notes = subprocess.run(
                         ['skimnotes', 'get', '-format', 'text', filepath , '-']
                         , text=True, capture_output=True
                        ).stdout

                note_iter = iter(re.split(r'^\* ([\w ]*, page \d+)$', notes
                                                      , flags=re.MULTILINE)[1:])
                tmp_result = set()
                for heading, note in zip(note_iter, note_iter):
                    if any((st_:= search_term) in heading or search_term in note
                                                  for search_term in args.note):
                        tmp_result.add(f"\t{heading}: found \"{st_}\"\n"
                                                        f"\t{note.strip()}\n\n")
                result += "".join(tmp_result)

            if result:
                print(f"{filepath}:\n{result}")

        except OSError as e:
            print(f"ERROR: {e.strerror}: '{e.filename}'", file=sys.stderr)
            sys.exit(e.errno)
