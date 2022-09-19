#!/usr/bin/env python3
# written by nathan sinclair

import sys
import re
import subprocess

from argparse import ArgumentParser
from itertools import chain
from pathlib import Path

from bibtex_entry import BibTeXEntry, FormatError

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-r', '--recursive', action='store_true'
                                         , help="recurse on each sub-directory")
    parser.add_argument('-y', '--type', action='store_true'
                                     , help="show the BibTeX type of each file")
    parser.add_argument('-c', '--citekey', action='store_true'
                                         , help="show the citekey of each file")
    parser.add_argument('-t', '--tag', action='append'
                , metavar=('TAG'), help="show the content of TAG for each file")
    parser.add_argument('-ht', '--hashtags', action='store_true'
              , help="show the hashtags in the notes and keywords of each file")
    parser.add_argument('-cht', '--collatehashtags', action='store_true'
              , help="show a collated list of all hashtags in the notes and "
              "keywords of all files")
    parser.add_argument('target', nargs='*', default=['.']
                                 , help="files (or directories containing them) "
                                 "with BibTeX entries to be printed")
    args = parser.parse_args()

    if args.collatehashtags:
        all_hashtags = set()
    if args.hashtags or args.collatehashtags:
        HASHTAG_RE = re.compile(r'#\w+(?:(:\d+)|(\(.*?\)))?')

    GLOB_PAT = '**/*.pdf' if args.recursive else '*.pdf'
    for filepath in chain.from_iterable(tp.glob(GLOB_PAT)
                                 if (tp := Path(targetname)).is_dir() else (tp,)
                                 for targetname in args.target):
        try:
            bib = BibTeXEntry.from_xattr(filepath)

            print(f"{filepath.name}:", file=sys.stderr)

            if args.hashtags or args.collatehashtags:
                file_hashtags = set()
                if hasattr(bib, 'keywords'):
                    file_hashtags.update(match.group()
                                 for match in HASHTAG_RE.finditer(bib.keywords))
                notes = subprocess.run(
                          ['skimnotes', 'get', '-format', 'text', filepath, '-']
                          , text=True, capture_output=True
                        ).stdout
                file_hashtags.update(match.group()
                                        for match in HASHTAG_RE.finditer(notes))
                if file_hashtags:
                    if args.hashtags:
                        print(f"\thashtags: {' '.join(file_hashtags)}")
                    if args.collatehashtags:
                        all_hashtags.update(file_hashtags)

            if bib is None:
                print('\tNo BibTeX entry attached to file\n', file=sys.stderr)
                continue

            if args.type:
                print(f"\ttype: {bib.type}")
            if args.citekey:
                print(f"\tcitekey: {bib.citekey}")
            if args.tag:
                for tag in args.tag:
                    if hasattr(bib, tag):
                        print(f"\t{tag} = {{{getattr(bib, tag)}}}")
                    else:
                        print(f"\t{tag}: NO SUCH TAG")


            if not (args.type or args.citekey or args.tag or args.hashtags\
                    or args.collatehashtags):
                print(bib)
            print(flush=True) # if &> file - this interleaves stdout and stderr
    
        except OSError as e:
            print(f"{e.filename}: {e.strerror}", file=sys.stderr)
            sys.exit(e.errno)
    # end loop iterating files

    if args.collatehashtags:
        print(f"Collated Hashtags:\n\t{' '.join(all_hashtags)}")
