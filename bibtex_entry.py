#!/usr/bin/env python3
# written by Nathan Sinclair
import re

from xattr import xattr
from pathlib import Path
import errno

class FormatError(Exception): pass

class BibTeXEntry:
    XATTR_KEY = 'sinclair_reffer_bibtex_entry'
    ENTRY_TEMPLATE = '@article{,\n@book{,\n@inbook{,\n@booklet{,\n@incollection{,\n@inproceedings{,\n@mastersthesis{,\n@manual{,\n@misc{,\n@phdthesis{,\n\tauthor = {},\n\tdoi = {},\n\tedition = {},\n\teditor = {},\n\tjournal = {},\n\tkeywords = {},\n\tnumber = {},\n\tpages = {1--2},\n\tpublisher = {},\n\tschool = {},\n\ttitle = {},\n\turl = {},\n\tvolume = {},\n\tyear = {}\n}'

    # type string stored in group('type')
    TYPE_RE = re.compile(r'@(?P<type>\w+)\s*\{')
    # citekey string stored in group('citekey')
    CITEKEY_RE = re.compile(r'\s*(?P<citekey>[-_:\w]*)\s*,')
    # name stored in group('name') content in group('braced_text') or group('number')
    TAG_RE =  re.compile(r'\s*(?P<name>[\w-]+)\s*=\s*([\{\"](?P<braced_text>.*?)[\}\"]|(?P<number>\d+))\s*(?:,\s*\}|,|\s+\})')

    def __init__(self, bibdict:dict):
        # ???? if citekey or type not in bibdict raise Exception 
        for tag, value in bibdict.items():
            setattr(self, tag, value)

    @classmethod # Alternative constructor
    def from_str(cls, bibstr:str, pos=0, *, return_end=False):
        """ Quasi-parse the next bibtex entry in bibstr starting at/after pos
            :param bibstr: a string expected to contain a bibtex entry
            :param pos: the position in bibstr to start searching for the entry
            :returns: a BibTexEntry OR a tuple (BibTeXEntry, endpos)
            :raises FormatError: arg[0] == position of last consumed character
        """
        type_match = cls.TYPE_RE.search(bibstr, pos)
        if not type_match:
            return None if not return_end else (None, pos)
        entry_dict = {'type':type_match.group('type')}
        pos = type_match.end()

        citekey_match = cls.CITEKEY_RE.match(bibstr, pos)
        if not citekey_match:
            raise FormatError(pos)
        entry_dict['citekey'] = citekey_match.group('citekey')
        pos = citekey_match.end()

        last_letter = "" # just in case the very first tag is malformed
        while tag_match := cls.TAG_RE.match(bibstr, pos):
            entry_dict[tag_match.group('name')]= tag_match.group('braced_text')\
                                              if tag_match.group('braced_text')\
                                              else tag_match.group('number') 

            pos = tag_match.end()
            last_letter = tag_match.group(0)[-1]

        if last_letter != '}':
            raise FormatError(pos)
        
        return cls(entry_dict) if not return_end else (cls(entry_dict), pos)

    @classmethod # Alternative constructor
    def from_xattr(cls, filepath):
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(errno.ENOENT, "File not Found"
                                                                , str(filepath))
        if (x_ := xattr(filepath)).has_key(cls.XATTR_KEY):
            return cls.from_str(x_.get(cls.XATTR_KEY).decode())
        else:
            return None

    @classmethod
    def read_entries(cls, bibstr:str):
        """
            :param bibstr: a sequence of bibtex entries
            :yields: BibTeXEntry objects
            :raises FormatError: With position of last consumed character
        """
        pos = 0
        entry, pos = cls.from_str(bibstr, pos, return_end=True)
        while entry:
            yield entry
            entry, pos = cls.from_str(bibstr, pos, return_end=True)

    def inject(self, filepath) -> None:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(errno.ENOENT, "File not Found"
                                                                , str(filepath))
        xattr(filepath).set(self.XATTR_KEY, repr(self).encode())

    def autoset_citekey(self) -> None:
        if 'author' in vars(self):
            name = re.match(r'\s*(?P<name>\w+)'
                                            , self.author).group('name').lower()
        else:
            name = ''
        year = vars(self).get('year', '') # string expected
        self.citekey = name + year

    def __str__(self):
        tags = [tag for tag in vars(self).keys() - {'citekey', 'type'}]
        tags.sort()
        result = f'@{self.type}{{{self.citekey},\n\t'\
             + ',\n\t'.join(f'{name} = {{{vars(self).get(name)}}}' for name in tags)\
             + ' \n}' # that space is important to resolve an ambiguity in
                      # in regular expressions that quasi parse BibTeX entries
        return result
        
    def __repr__(self):
        return self.__str__().replace('\n','').replace('\t','').replace(' = ', '=')
