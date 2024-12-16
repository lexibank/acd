"""
LanguageTable:PMP 674
LanguageTable:PAN 506
LanguageTable:POC 368
LanguageTable:PPh 183
LanguageTable:PWMP 183
LanguageTable:OC 137
LanguageTable:WMP 103
LanguageTable:Form. 76
LanguageTable:CMP 57
LanguageTable:PCEMP 47
LanguageTable:MP 23
LanguageTable:CEMP 23
LanguageTable:SHWNG 6
LanguageTable:PCMP 5
LanguageTable:EMP 3

"""
import collections

from tqdm import tqdm
import newick
from lexibank_acd import Dataset

import acdparser

TREE = newick.loads(acdparser.TREE)[0]


def node_to_root():
    def get_all_paths(node):
        if len(node.descendants) == 0:
            return [[node.name]]
        return [
            [node.name] + path for child in node.descendants for path in get_all_paths(child)
        ]
    def yield_subsets(s):
        for i in range(len(s)):
            yield s[0:i+1]
    res = []
    for p in get_all_paths(TREE):
        res.extend(list(yield_subsets(p)))
    return {p[0]: p for p in [list(reversed(s)) for s in set([tuple(r) for r in res])]}


N2R = node_to_root()


def closest_pl(group, pls):
    #
    # follow the branch leading to the corresponding pl up to the root,
    # first node in pls is the "best".
    #
    for pl in N2R.get(group,  []):
        if pl in pls:
            return pl


def run(args):
    from pycldf.ext.markdown import CLDFMarkdownText

    missing = collections.Counter()

    class TestMarkdown(CLDFMarkdownText):
        def render_link(self, cldf_link):
            try:
                self.get_object(cldf_link)
            except:
                missing.update(['{}:{}:{}'.format(cldf_link.label, cldf_link.table_or_fname, cldf_link.objid)])

    cldf = Dataset().cldf_reader()
    cols = []
    for t in cldf.tables:
        try:
            tname = cldf.get_tabletype(t)
        except ValueError:
            tname = None
        tname = tname or str(t.url)
        for col in t.tableSchema.columns:
            if col.common_props.get('dc:conformsTo') == 'CLDF Markdown':
                cols.append((tname, col.name))

    for t, c in cols:
        args.log.info('validating CLDF Markdown in {}:{}'.format(t, c))
        for obj in tqdm(cldf[t]):
            if obj[c] and '[' in obj[c]:
                TestMarkdown(obj[c], cldf).render()

        for k, v in missing.most_common():
            args.log.warning('Not found {}:{}'.format(k, v))
        missing = collections.Counter()

    return

    #
    # forms of dialects duplicated for the parent language as well
    #
    langs = {r['ID']: r for r in cldf['LanguageTable']}
    dialects = {r['ID']: r['Dialect_Of'] for r in cldf['LanguageTable'] if r['Dialect_Of']}

    forms_by_lang = collections.defaultdict(set)
    for form in cldf['FormTable']:
        forms_by_lang[form['Language_ID']].add(form['Value']+form['Parameter_ID'])

    for did, lid in dialects.items():
        for form in forms_by_lang[did]:
            if form in forms_by_lang[lid]:
                print('yes')
            else:
                print('no')

    return

    csets = collections.defaultdict(lambda: collections.defaultdict(list))
    for pf in cldf['protoforms.csv']:
        if pf['Inferred'] == False:
            csets[pf['Cognateset_ID']][pf['Proto_Language']].append(pf['ID'])

    #print(len(csets))
    to_check = dict([(k, cs) for k, cs in csets.items() if all(len(v) == 1 for v in cs.values())])

    print(to_check['30607'])
    return

    lmap = {l['ID']: l['Group'] for l in cldf['LanguageTable']}
    fmap = {f['ID']: (lmap[f['Language_ID']], f['Form']) for f in cldf['FormTable']}

    # Cognates should grouped with the "closest" reconstruction.

    for c in cldf['CognateTable']:
        # look up form and language subgroup:
        if c['Cognateset_ID'] in to_check and (c['Reconstruction_ID']):
            pl = 'P' + fmap[c['Form_ID']][0]
            pf = to_check[c['Cognateset_ID']]
            closest = closest_pl(pl, pf)
            if closest and (c['Reconstruction_ID'] not in pf[closest]):
                rpl = None
                for ppl, rids in pf.items():
                    if ppl != closest:
                        if c['Reconstruction_ID'] in rids:
                            rpl = ppl
                            break
                print('{}: witness {} from group {} listed for reconstruction {}, not {}, {}'.format(c['Cognateset_ID'], fmap[c['Form_ID']][1], pl, rpl, closest, list(pf.keys())))
