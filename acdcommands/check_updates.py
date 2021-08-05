"""

"""
from acdparser import updates

from lexibank_acd import Dataset


def run(args):
    ds = Dataset()
    for p in sorted(ds.raw_dir.joinpath('updates').glob('*.odt'), key=lambda p_: p_.stem):
        for etymon, forms, note in updates.parse(p, verbose=True):
            pass
