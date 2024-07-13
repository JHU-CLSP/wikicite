from dataclasses import dataclass
from typing import *
from collections import defaultdict

import mwparserfromhell


@dataclass
class Citation:
    # citations extracted from the same wikipedia reference line should have the same key
    key: int
    # its article idx and element idx
    locator: Tuple[int, int] | None = None
    ref_type: str | None = None
    title: str | None = None
    long: str | None = None
    short: str | None = None

    @property
    def is_empty_citation(self):
        # no short/long content
        return self.short is None and self.long is None

    def to_dict(self):
        return {
            'ref_type': self.ref_type, 'title': self.title, 'long': self.long, 'short': self.short,
            'article_idx': self.locator[0], 'element_idx': self.locator[1]
        }


def process_one_citation(citation):
    # read the megawika v2 citation format; parse one citation.

    # from wikicode we can obtain structured information about the citation,
    # pretty much everything except for the scraped text from url
    wikicode = mwparserfromhell.parse(citation['content'])
    # wikicode is citation based. To know more about templates, here is a reference
    # https://en.wikipedia.org/wiki/Wikipedia:Citation_templates

    cite = Citation(
        hash(citation['content']),
        long=citation['source_text'],
        locator=(citation['article_idx'], citation['element_idx'])
    )
    # one citation could contain more than one template; they might be mistakes.
    # this script iterates over these templates, and take the first template
    # of "ref" type as the reference template. Other templates will be ignored.
    for template in wikicode.filter_templates():
        # template name
        tn = template.name.strip().lower()
        while '  ' in tn:
            tn = tn.replace('  ', ' ')
        if tn in ['nbsp', '!']:
            continue
        if tn == 'refn':
            # this is for footnote; we ignore footnote
            cite.ref_type = 'refn'
            return cite

        if tn.startswith('cite') or tn == 'r':
            # template starts with "cite" will be simply treated as citation
            # this could be wrong. future should consider enumerate the names instead
            cite.ref_type = tn
        else:
            # otherwise ignore this item; false positives exist
            continue

        for line in template.params:
            line = line.strip()
            if line.startswith('quote='):
                cite.short = line[len('quote='):].strip()
            if line.startswith('title='):
                cite.title = line[len('title='):].strip()
        # we found the citation. exit the loop
        return cite


def process_citations(citations: List[dict]) -> List[Citation]:
    # one citation could appear multiple times if it contains multiple urls
    # therefore we group them, using the content as the key
    groups = defaultdict(list)
    for cite_dict in citations:
        cite = process_one_citation(cite_dict)
        if cite is None or cite.is_empty_citation:
            continue
        groups[cite.key].append(cite)

    ret = []
    for li in groups.values():
        # in each group, keep the one with the longest long citation
        li.sort(key=lambda c: len(str(c.long)))
        ret.append(li[-1])
    return ret
