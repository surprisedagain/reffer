#!/usr/bin/env python3
# written by nathan sinclair

import subprocess
import re
import sys, os, errno
import textwrap

from argparse import ArgumentParser
from itertools import chain
from pathlib import Path
from textwrap import TextWrapper

from bibtex_entry import BibTeXEntry, FormatError

TEXT_LAYOUT = TextWrapper(initial_indent='\t', subsequent_indent='\t'
                                                            , expand_tabs=False)
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
            if not filepath.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT)
                                                                     , filepath)
            result = ""
            if args.keyword or args.tag or args.citekey:
                # need to search some component of bibliography
                if bib := BibTeXEntry.from_xattr(filepath):

                    if args.citekey: # search citekey
                        if args.citekey.casefold() in bib.citekey.casefold():
                            result += f"\tcitekey: {bib.citekey}\n"
                        elif args.all:
                            continue # on to next file

                    if args.keyword: # search keywords
                        junct = all if args.all else any
                        if junct(search_term.casefold()
                                      in getattr(bib, 'keywords', '').casefold()
                                      for search_term in args.keyword):
                            result += f"\tkeywords = {{{bib.keywords}}}\n"
                        elif args.all:
                            continue # on to next file

                    if args.tag: # search tags
                        tmp_result = set()
                        all_criteria = True
                        for search_tag, search_term in args.tag:
                            if search_term.casefold() \
                                      in getattr(bib, search_tag,'').casefold():
                                tmp_result.add(f"\t{search_tag} = "
                                            f"{{{getattr(bib, search_tag)}}}\n")
                            elif args.all:
                                all_criteria = False
                                break
                        if args.all and not all_criteria:
                            continue # on to next file
                        result += "".join(tmp_result)

                else: # no BibTeXEntry attached to file
                    print(f"{filepath}:\n\tNo BibTeX entry attached to file"
                                                              , file=sys.stderr)

            # bibliography search finished - may search notes next
            if args.note:
                notes = subprocess.run(
                         ['skimnotes', 'get', '-format', 'text', filepath , '-']
                         , text=True, capture_output=True
                        ).stdout

                note_iter = iter(re.split(r'^\* ([\w ]*, page \d+)$', notes
                                                      , flags=re.MULTILINE)[1:])
                tmp_result = set()
                for heading, note in zip(note_iter, note_iter):
                    if any((st_:= search_term.casefold()) in heading.casefold()
                                                  or st_ in note.casefold()
                                                  for search_term in args.note):
                        tmp_result.add(f"\t{heading}: found \"{st_}\"\n"
                                                        + TEXT_LAYOUT.fill(note)
                                                        + "\n\n")
                if tmp_result:
                    result += "".join(tmp_result)
                elif args.all:
                    continue # on to next file

            if result:
                print(f"{filepath}:\n{result}")

        except OSError as e:
            print(f"ERROR: {e.strerror}: '{e.filename}'", file=sys.stderr)
            sys.exit(e.errno)
