"""

"""
import re

from pybtex.database import parse_string

from lexibank_acd import Dataset


def run(args):
    ds = Dataset()
    bib = parse_string(ds.etc_dir.read('sources.bib'), 'bibtex')
    bib = {v.fields['key']: v for v in bib.entries.values()}

    for row in ds.etc_dir.read_csv('languages.tsv', delimiter='\t', dicts=True):
        for ref in re.split(';', row['Source']):
            ref = ref.strip()
            #if ref in bib:
            #    print(ref)
            if ref and ref not in bib:
                print('{}\t{}'.format(row['ID'], ref))