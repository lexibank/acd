"""

"""
import re
import collections

from lxml import etree

from acdparser.updates import qname
from clldutils.misc import nfilter

from lexibank_acd import Dataset

LANGS = """\
AA: Ayta Abellen (Stone 2019)
AgtaE: Eastern Cagayan Agta (Nickell and Nickell 1987)
AGU: Agutaynen (Caabay, Edep, Hendrickson and Melvin 2014)
AKL: Aklanon (Zorc 1969)
Arta: Arta (Reid 1989, Kimoto n.d.)
BKD: Binukid (Otanes and Wrigglesworth 1992)
BKL: Bikol (Mintz and Britanico 1985)
BM: Bolaang Mongondow (Dunnebier 1951)
BON: Bontok (Reid 1976)
BtkP: Palawan Batak (Warren 1959)
CEB: Cebuano (Wolff 1971)
DgtC: Casiguran Dumagat (Headland and Headland 1974)
HAN: Hanunóo (Conklin 1953)
HLG: Hiligaynon (Motus 1971)
IBG: Ibanag (McFarland 1977)
IBL: Ibaloy (Ballard 2011)
IBT: Ibatan (Maree, Tomas, and Maree 2012)
IFG: Ifugaw (Lambrecht 1978)
IfgBt: Batad Ifugaw (Newell 1993)
ILK: Ilokano (Rubino 2000)
ISG: Isneg (Vanoverbergh 1972)
ITB: Itbayaten (Yamada 1976, 2002)
ITW: Itawis (Tharp and Natividad 1976)
KNK: Kankanay/Kankanaey (Vanoverbergh 1933)
KLY: Keley-i (Hohulin, Hohulin and Maddawat 2018)
KPG: Forman (1971)
MAR: Maranao (McKaughan and Macaraya 1968)
MbS: Sarangi Manobo (Dubois 1976)
MSB: Masbatenyo (Wolfenden 2001)
MSK: Mansaka (Svelmoe and Svelmoe 1990)
PGS: Pangasinan (Benton 1971)
PLW: Macdonald (2011)
RBL: Romblomanon (Newell 2006)
SblBt: Botolan Sambal (Minot, Houck, and Quinsay 1968)
SGR: Sangir (Steller and Aebersold 1959)
TAG: Tagalog (English 1986)
TBL: Tboli (Awed, Underwood and van Wynen 2004)
TbwC: Central Tagbanwa (Scebold 2003)
TIR: Tiruray (Schlegel 1971)
TSG: Tausug (Hassan, Ashley and Ashley 1994)
TTB: Tontemboan (Schwarz 1908)
WRY: Waray-Waray (Abuyen 2000)
WBM: Western Bukidnon Manobo (Elkins 1968)
Yami: Yami (Rau, Dong and Chang 2012)"""

def get_langs():
    p = re.compile('(?P<abbr>[^:]+):\s+(?P<name>[^(]+)\((?P<ref>[^)]+)\)')
    res = {}
    for line in LANGS.split('\n'):
        m = p.fullmatch(line)
        res[m.group('abbr')] = m.groupdict()
    return res


def witness(line, llid):
    lid, form, gloss = line.split('\t')
    lid = lid or llid
    assert lid
    if gloss.startswith("‘") and "‘" not in gloss[1:]:
        gloss = gloss[1:]
    if gloss.endswith("’") and "’" not in gloss[:-1]:
        gloss = gloss[:-1]
    return lid, form, gloss.strip()


def etymon(line):
    no, _, rem = line.partition('*')
    assert re.fullmatch('[0-9]{3}\.', no.strip())
    no = int(no.strip()[:-1])
    form, _, gloss = rem.partition("‘")
    if gloss.endswith(')'):
        gloss, _, rem = gloss.partition('(')
        # FIXME:  (dbl. *inut)
        gloss = gloss.strip()
    if gloss.endswith('.'):
        gloss = gloss[:-1]
    assert gloss.endswith("’"), line
    return no, form.strip(), gloss[:-1].strip()


def iter_cogns(p, langs, witn):
    lid = None
    no, pform, pgloss, note, witnesses = None, None, None, None, []
    for line in p.read_text(encoding='utf8').split('\n'):
        line = line.rstrip()
        if line == 'REFERENCES':
            break
        if not line:
            continue
        if line.startswith('\t'):
            assert lid
            witn.update([lid])
            assert len(line.split('\t')) == 3, line
            witnesses.append(witness(line, lid))
        elif line.startswith('NOTE:'):
            note = line.replace('NOTE:', '').strip()
        elif line.split('\t')[0] in langs:
            witn.update([line.split('\t')[0]])
            lid = line.split('\t')[0]
            assert len(line.split('\t')) == 3, line
            witnesses.append(witness(line, lid))
        elif re.match('[0-9]{3}\.', line):
            if pform:
                yield no, pform, pgloss, note, witnesses
                no, pform, pgloss, note, witnesses = None, None, None, None, []
            assert "‘" in line and "*" in line, line
            no, pform, pgloss = etymon(line)
        elif re.fullmatch('\((a|b)\)', line):
            pass
        else:
            raise ValueError(line)
    if pform:
        yield no, pform, pgloss, note, witnesses


def run(args):
    langs = get_langs()
    witn = collections.Counter()
    ds = Dataset()
    pph_forms = {r['ID']: r['Form'].replace('*', '') for r in ds.cldf_reader()['CognatesetTable'] if r['Proto_Language'] == 'PPh'}
    wn = collections.Counter(r['Cognateset_ID'] for r in ds.cldf_reader()['CognateTable'])
    pph_forms = {v: (wn[k], k) for k, v in pph_forms.items()}
    known = 0
    for cog in iter_cogns(ds.raw_dir.joinpath('updates', '2021-11-15', 'content.txt'), langs, witn):
        no, pform, pgloss, note, witnesses = cog
        if pform in pph_forms:
            nw, id_ = pph_forms[pform]
            print('{}\t*{}\t{}\t{}/{}\thttps://acd.clld.org/cognatesets/{}'.format(no, pform, pgloss, len(witnesses), nw, id_))

            #if len(witnesses) < pph_forms[pform]:
            #    known += 1
            #    witnesses = '\n'.join(['\t{}\t{}\t‘{}‘'.format(l, f.replace('__it__', '').replace('__/it__', ''), g) for l, f, g in witnesses])
            #    print("""
#PPh\t*{}\t‘{}‘\t[{}]
#{}
#{}
#""".format(pform, pgloss, no, witnesses, '\nNOTE: {}\n'.format(note) if note else ''))

    #print(known)
    #assert len(witn) == len(langs), '{}'.format(set(langs) - set(witn))
    #for k, v in witn.most_common():
    #    print(k, v)








def text(p):
    res = [p.text]
    for i, e in enumerate(p.iter()):
        if i == 0 and e.text and e.text == res[0]:
            continue
        t = e.text
        if t is not None and t.strip() and (e.attrib.get(qname('text', 'style-name')) or 'x') in 'T2 T3 T4 T6 T10 T19':
            t = '__it__{}__/it__'.format(t.strip())
        res.extend([t, e.tail])
    res = '\t'.join(nfilter([s.strip() for s in res if s])).strip()
    res = res.replace(" ‘__/it__\t", "__/it__\t‘")
    return res


def _run(args):
    ds = Dataset()
    doc = etree.fromstring(
        ds.raw_dir.joinpath('updates', '2021-11-15', 'content.xml').read_bytes())
    in_cogs = False
    for p in doc.findall('.//{}'.format(qname('text', 'p'))):
        if p.text and p.text.startswith('001'):
            in_cogs = True
        if in_cogs:
            t = text(p)
            if re.match(r'[0-9]{3}\.', t):
                print('')
            if t:
                print(t)
