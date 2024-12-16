import typing
import pathlib
import functools
import itertools
import collections
import unicodedata

import attr
import newick
import pylexibank
from clldutils.misc import data_url
from clldutils.markup import MarkdownLink
from pycldf import Dataset as CLDFDataset
from pycldf.ext.markdown import CLDFMarkdownLink
from csvw.metadata import Datatype
from pyetymdict.dataset import Language as BaseLanguage, Dataset as BaseDataset

FORM_FIXES = {  # The only reconstruction starting with "L". Clearly a typo.
    'LapaR₂': 'lapaR₂',
}
DISAMBIGUATION_MARKERS = ['₁', '₂', '₃', '₄', '₅']
PROTO_DESC = {
    'PMP': 'Malayo-Polynesian = all AN languages outside Taiwan.',
    'PWMP':
        'Western Malayo-Polynesian = the AN languages of the Philippines, Borneo, the Malay '
        'peninsula, and islands in peninsular Thailand and Burma, Sumatra, Java and its '
        'satellites, Bali, Lombok, western Sumbawa, Sulawesi, Palauan and Chamorro of western '
        'Micronesia, the seven or eight Chamic languages of mainland Southeast Asia and Hainan '
        'Island, and Malagasy.',
    'PPH': 'Philippine languages.',
    'PCEMP': 'Central-Eastern Malayo-Polynesian = CMP + EMP.',
    'PCMP':
        'Central Malayo-Polynesian = the AN languages of the Lesser Sunda islands and the '
        'southern and central Moluccas of eastern Indonesia.',
    'PEMP': 'Eastern Malayo-Polynesian = SHWNG + OC.',
    'PSHWNG':
        'South Halmahera-West New Guinea = the 30‒40 AN languages of southern Halmahera and '
        'the northern Bird’s Head peninsula of New Guinea.',
    'POC':
        'Oceanic = the roughly 460 AN languages of Melanesia, Micronesia, and Polynesia except '
        'Palauan and Chamorro of western Micronesia.',
    'Form.':
        'Unlike these subgroup labels, “Formosan” is used as a cover term for the aboriginal '
        'languages of Taiwan which appear to belong to at least nine primary branches of the AN '
        'language family. In addition, PWMP may not be a valid subgroup, and some forms that are '
        'currently assigned to it may have been found in PMP.',
}
TREE = newick.loads('(Form.,((PPH)PWMP,(PCMP,(PSHWNG,POC)PEMP)PCEMP)PMP)PAN;')[0]
DESCRIPTIONS = {
    'CognatesetTable':
        "Comparisons with regular sound correspondences and close semantics. If there are "
        "additional forms that are strikingly similar but irregular, or that show strong semantic "
        "divergence, these are are added in a note. Every attempt is made to keep the comparison "
        "proper free from problems.\n\nBecause many reconstructed morphemes contain smaller "
        "submorphemic sound-meaning associations of the type that Brandstetter (1916) called "
        "‘roots’ (Wurzeln), these elements are listed as cognate sets, too. They are marked "
        "with a true value for the 'Is_Root' property of the linked, reconstructed form.\n\n"
        "The roots listed here thus amount to a continuation of the data set presented in "
        "Blust 1988.",
    'cf.csv':
        "The ACD includes five additional categories of groups of forms, called 'near cognates', "
        "'noise', 'roots', 'loans' and 'also'. These are marked with respective values in the "
        "'Category' column.\n\n"
        "'Near cognates' are forms that are strikingly similar but irregular, and "
        "which cannot be included in a note to an established reconstruction. Stated differently, "
        "these are forms that appear to be historically related, but do not yet permit a "
        "reconstruction.\n\nThe 'noise' (in the information-theoretic sense of meaningless data "
        "that can be confused with a true signal) category lists chance resemblances. Given the "
        "number of languages being compared and the number of forms in many of the sources, forms "
        "that resemble one another in shape and meaning by chance will not be uncommon, and the "
        "decision as to whether a comparison that appears good is a product of chance must be "
        "based on criteria such as\n- how general the semantic category of the form is (e.g. "
        "phonologically corresponding forms meaning ‘cut’ are less diagnostic of relationship "
        "than phonologically corresponding forms for particular types of cutting),\n- how richly "
        "attested the form is (if it is found in just two witnesses the likelihood that it is a "
        "product of chance is greatly increased),\n- there is already a well-established "
        "reconstruction for the same meaning.\n\nThus, the search process that results in valid "
        "cognate sets inevitably turns up other material that is superficially appealing, but is "
        "questionable for various reasons. To simply dispose of this ‘information refuse’ would be "
        "unwise for two reasons. First, further searching might show that some of these "
        "questionable comparisons are more strongly supported than it initially appeared. Second, "
        "even if the material is not upgraded through further comparative work it is always "
        "possible that some future researcher with different standards of evaluation will stumble "
        "upon some of these comparisons and claim that they are valid, but were overlooked in the "
        "ACD. By including a module on ‘Noise’ we can show that we have considered and rejected "
        "various possibilities that might be entertained by others.\n\nBecause many reconstructed "
        "morphemes contain smaller submorphemic sound-meaning associations of the type that "
        "Brandstetter (1916) called ‘roots’ (Wurzeln), these elements are included in the 'roots' "
        "category. The roots listed here thus amount to a continuation of the data set presented "
        "in Blust 1988.\n\nRoots are not listed as regular cognate sets, because the "
        "reconstructions are not explicitly assigned to a proto-language.\n\n"
        "Loanwords are a perennial problem in historical linguistics. When they involve morphemes "
        "that are borrowed between related languages they can provoke questions about the "
        "regularity of sound correspondences. When they involve morphemes that are borrowed "
        "between unrelated languages they can give rise to invalid reconstructions. "
        "Dempwolff (1934-38) included a number of known loanwords among his 2,216 "
        "‘Proto-Austronesian’ reconstructions in order to show that sound correspondences are "
        "often regular even with loanwords that are borrowed relatively early, but he marked these "
        "with an ‘x’, as with *xbazu ‘shirt’, which he knew to be a Persian loanword in many of "
        "the languages of western Indonesia, and (via Malay) in some of the languages of the "
        "Philippines. However, he overlooked a number of cases, such as *nanas ‘pineapple’ (an "
        "Amazonian cultigen that was introduced to insular Southeast Asia by the Portuguese). "
        "Since widely distributed loanwords can easily be confused with native forms it is useful "
        "to include them in the dictionary.\n\nA fairly careful (but inevitably imperfect) attempt "
        "has been made to identify and document loanwords with a distribution sufficient to "
        "justify a reconstruction on one of the nine levels of the ACD, if treated erroneously "
        "as native. While this has been done wherever the possibility of confusion with native "
        "forms seemed real, there is no reason to include obvious loans that would never be "
        "mistaken for native forms.\n\nThis issue is especially evident in the Philippines, where "
        "hundreds of Spanish loanwords from the colonial period that began late in the 16th "
        "century, are scattered from at least Ilokano in northern Luzon to the Bisayan languages "
        "of the central Philippines and some of the languages of Mindanao (as Subanon). "
        "Comparisons like Ilokano kamarón ‘prawn’, Cebuano kamarún ‘dish of shrimps, split and "
        "dipped in eggs, optionally mixed with ground meat’ < Spanish camarón ‘shrimp’, or "
        "Ilokano kalábus ‘jail, prison’, Cebuano kalabús, kalabúsu ‘jail; to land in prison, in "
        "jail’ < Spanish calabozo ‘dungeon’ seem inappropriate for inclusion in LOANS, but "
        "introduced plants have generally been admitted. Some of these, as ‘tomato’ may be widely "
        "known as New World plants that were introduced to the Philippines by the Spanish, but "
        "others, as ‘chayote’, may be less familiar. As already noted, Dempwolff (1938) posited "
        "‘Uraustronesisch’ *nanas and *kenas as doublets for ‘pineapple’, completely overlooking "
        "the fact that this is an Amazonian plant that could hardly have been present in the "
        "Austronesian world before the advent of the colonial period. This example shows that "
        "errors in the semantic domain of plant names can sometimes escape detection by scholars "
        "who are otherwise known for their careful, meticulous work, and for this reason all "
        "borrowed cognate sets involving plant names are documented as loanwords to avoid any "
        "possible misinterpretation.\n\n"
        "The last category, 'also', groups forms related to a particular cognate set. These forms "
        "typically show some kind of irregularity with respect to the proposed reconstruction, but "
        "provide context to evaluate the validity of the cognate set.",
}
GRAPHEMES = [
    'a', 'b', 'c', 'C', 'd', 'e', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'N', 'ñ', 'ŋ', 'o',
    'p', 'q', 'r', 'R', 's', 'S', 't', 'u', 'w', 'y', 'z']


def fixed_form(f):
    if not f:
        return f
    if f in FORM_FIXES:
        return FORM_FIXES[f]
    if f.startswith('*') and f[1:] in FORM_FIXES:
        return '*' + FORM_FIXES[f[1:]]
    return f


def get_initial(form):
    # Compute the first grapheme of a reconstruction:
    first = form.replace('*', '').replace('-', '').replace('(', '').replace('<', '')[0]
    if first not in GRAPHEMES:
        # Do away with combining characters!
        first = unicodedata.normalize('NFD', first)[0]
    assert first in GRAPHEMES
    return first


def infer_protoforms(sets):  # Factor out into acdcommand
    """
    Counts are shown below the proto-language index line. In counting numbers of entries for any
    given proto-language it is necessary to distinguish explicit from implicit reconstructions.
    Explicit reconstructions are always marked with a proto-form which is assigned to a stated
    proto-language. Implicit reconstructions, on the other hand, are logically implied at various
    levels by the structure of the family tree, but are not overtly indicated. Thus,
    PAN *enem 'six' contains three explicit reconstructions, each of which is required because
    it differs in shape, in meaning, or in both from its antecedent form:

        PAN	*enem	'six'
        PEMP	*onəm	'six'
        POC	*onom	'six'

    However, since PAN *enem evidently persisted in the same shape and meaning until the formal
    changes seen in PEMP *onəm, PMP *enem 'six', and PCEMP *enem 'six' are automatically supplied
    by the structure of the phylogeny (similar reflexes in CMP languages likewise imply
    PCMP *enem 'six'). Likewise, since PEMP *onəm evidently persisted until the innovation which
    produced POC *onom, PSHWNG *onəm 'six' is also implied. The highest-order reconstruction in
    a cognate set is thus always an explicit reconstruction, although any other proto-form that
    has undergone formal or semantic change from its antecedent is also explicitly indicated.
    """
    descendants, nodes = collections.defaultdict(set), {}
    for n in TREE.walk():
        nodes[n.name] = n
        descendants[n.name] = {nn.name for nn in n.walk()}

    protoforms = {s['proto_language']: (s['key'], s['gloss']) for s in sets}
    # We can only infer proto-forms when reflexes in a language of the corresponding group are
    # attested.
    attested = set()
    for s in sets:
        attested = attested.union({'P' + f['group'] for f in s['forms']})

    # Loop over the related reconstructions:
    for s in sets:
        excluded = set()
        for i, n in enumerate(nodes[s['proto_language']].walk()):
            if i:
                # Now we walk the descendants in the proto-language tree.
                if n.name in excluded:
                    continue

                if n.name in protoforms:
                    # There's an explicit variation of this reconstruction for this part of the
                    # tree; thus we exlude all descendants of this node from the search:
                    excluded = excluded.union(descendants[n.name])
                    continue

                if any(pl in attested for pl in descendants[n.name]):
                    # Reflexes are attested for a language that descended from this proto-language
                    yield s['id'], n.name, s['key'], s['gloss']


@attr.s
class Cognate(pylexibank.Cognate):
    Metathesis = attr.ib(
        default=False,
        metadata={
            'datatype': 'boolean',
            'dc:description':
                'Flag indicating that a process of metathesis is assumed, explaining the apparent '
                'irregularity of a cognate.',
        }
    )
    Assimilation = attr.ib(
        default=False,
        metadata={
            'datatype': 'boolean',
            'dc:description':
                'Flag indicating that a process of assimilation is assumed, explaining the '
                'apparent irregularity of a cognate.',
        }
    )
    Doublet_Comment = attr.ib(
        default=None,
        metadata={
            'dc:description': 'A comment about the doublet status of the reconstruction.',
        }
    )
    Doublet_Set = attr.ib(
        default=None,
        metadata={
            'dc:description':
                'Identifier of a set of variants that are independently supported by the '
                'comparative evidence. Doubletting that cannot be traced in any clear way to '
                'borrowing is extremely common in AN languages (Blust 2011), and an effort has '
                'been made to cross-reference doublets in the ACD wherever possible.',
        }
    )
    Disjunct_Comment = attr.ib(
        default=None,
        metadata={
            'dc:description': 'A comment about the disjunct status of the reconstruction.',
        }
    )
    Disjunct_Set = attr.ib(
        default=None,
        metadata={
            'dc:description':
                'Identifier of a set of variants that are supported only by allowing the overlap '
                'of cognate sets; i.e. only one reconstruction in a set of disjuncts can be '
                'consistent with the evidence, but it is unclear which one. A distinction is drawn '
                'between doublets (variants that are independently supported by the comparative '
                'evidence), and “disjuncts” (variants that are supported only by allowing the '
                'overlap of cognate sets). To illustrate, both Tagalog gumí ‘beard’ and Malay '
                'kumis ‘moustache’ show regular correspondences with Fijian kumi ‘the chin or '
                'beard’, but they do not correspond regularly with one another. Based on this '
                'evidence, it is impossible to posit doublets, since unambiguous support for both '
                'variants is lacking. However, since the Tagalog and Malay forms can each be '
                'compared with Fijian kumi, two comparisons can be proposed that overlap by '
                'including the Fijian form in both (like all Oceanic languages, Fijian has merged '
                'PMP *k and *g; in addition, it has lost final consonants) . The result is a pair '
                'of PMP disjuncts *gumi (based on Tagalog and Fijian) and *kumis (based on Malay '
                'and Fijian), either or both of which could be used to justify an independent '
                'doublet if additional comparative support is found.',
        }
    )


@attr.s
class Variety(BaseLanguage):
    Description = attr.ib(
        default=None,
        metadata={
            'dc:description':
                'For proto-languages that correspond to ACD reconstruction levels, a description '
                'of their extent is provided.',
            'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description'}
    )
    Dialect_Of = attr.ib(default=None)


class Forms(dict):
    def id(self, fid):
        return self[fid]['ID']

    def lname(self, fid, varieties):
        return varieties.name(self[fid]['Language_ID'])

    def form(self, fid):
        return self[fid]['Value']

    def meaning(self, fid):
        return self[fid]['Description']

    def labbr(self, fid, varieties):
        return varieties.abbr(self[fid]['Language_ID'])


def root2id(cldf) -> typing.Dict[str, str]:
    """
    :return: `dict` mapping root forms to cf set IDs.
    """
    roots = {row['Form'].lstrip('*'): row['ID'] for row in cldf['CognatesetTable'] if
             row['Contribution_ID'] == 'Root'}
    for k, v in {  # We register a couple of often referenced aliases:
        '-pak₁': '*-pak₁ (or *-paqak?)',
        '-tuk₂': '*-tuk₂ (or *-tuquk?)',
        '-kuŋ': '*-kuŋ (or *-kuquŋ?)',
        '-suk': '*-suk (or *suquk?)',
        '-bun': '*-bun (or *-bequn?)',
        '-luk': '*-luk (or *-luquk?)',
        '-tak₂': '*-tak₂ (or *-taqak?)',
        '-pik': '*-pik (or *-piqik?)',
        '-rit': '*-rit (or *-reclit?)',
        '-ŋeC': '*-ŋeC  (or *-ŋeqeC?)',
        '-Ruŋ': '*-Ruŋ (or *-Ruquŋ?)',
        '-NaR': '*-NaR (or *-NagaR?)',
        '-guŋ': '*-guŋ (or *-guquŋ?)',
        '-Cuk': '*-Cuk (or *-Cuquk?)',
        '-dek₁': '*-dek₁ (or *-deqek?)',
        '-pek': '*-pek (or *-peqek?)',
        '-let': '*-let (or *-leget?)',
    }.items():
        roots[k] = roots[v.lstrip('*')]
    return roots


class Varieties(dict):
    """
    Just a wrapper providing convenient access to language metadata during CLDF creation.
    """
    def __init__(self, writer):
        dict.__init__(self, {r['ID']: r for r in writer.objects['LanguageTable']})

    @functools.cached_property
    def proto_langs(self):
        return [id_ for id_, r in self.items() if r['Is_Proto']]

    def name(self, id_):
        return self[id_]['Name']

    def abbr(self, id_):
        return self[id_]['Abbr'] or None

    @functools.cached_property
    def abbr2id(self):
        return {r['Abbr']: r['ID'] for r in self.values() if r['Abbr']}


def main_reconstruction(rows):
    """
    The main reconstruction in a set of protoforms is the "highest-level" one; i.e. the proto-form
    for the earliest proto-language in the tree.
    """
    for n in TREE.walk():
        for row in rows:
            if row['Proto_Language'].upper() == n.name:
                return row
    raise AssertionError('No main reconstruction found')


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "acd"

    cognate_class = Cognate
    language_class = Variety

    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=('?', '-'),  # characters that denote missing data.
        strip_inside_brackets=True   # do you want data removed in brackets or not?
    )

    def fix_markdown(self, text, roots=None):
        if not text:
            return text

        abbrs, names = {}, {}
        for l in self.languages:
            if l['Abbr']:
                abbrs[l['Abbr']] = l['ID']
                abbrs[l['Abbr'].lower()] = l['ID']
            names[l['Name']] = l['ID']
        names["Sa’a"] = names["Sa'a"]
        names["Iloko"] = names["Ilokano"]
        lmap = {k: v for k, v in abbrs.items()}
        lmap.update(names)

        def link_languages(s):
            if not s:
                return None
            n, with_langs = '', False
            while '__language__' in s:
                with_langs = True
                pre, _, s = s.partition('__language__')
                n += pre
                assert '__' in s, s
                lname, _, s = s.partition('__')
                if lname in [
                    'Arabic',
                    'Portuguese', 'Dutch',
                    'Spanish',
                    'Sanskrit',  # https://glottolog.org/resource/languoid/id/sans1269
                    'Philippine',
                    'Tamil',  # https://glottolog.org/resource/languoid/id/tami1289
                    'Hindi',
                    'Persian',
                ]:
                    n += lname
                    continue
                if lname.lower() == 'gcph':
                    n += ('[Greater Central Philippine]'
                          '(https://glottolog.org/resource/languoid/id/grea1284)')
                    continue
                lid = lmap.get(lname)
                if not lid:
                    lid = lmap.get(lname.lower())
                    if not lid:
                        lid = lmap.get('p' + lname.lower())
                if lid:
                    n += '[{}](LanguageTable#cldf:{})'.format(lname, lid)
                else:
                    n += lname

            return (n + s).strip().replace('\n\n\n', '\n')

        def repl(ml):
            if ml.table_or_fname == 'LanguageTable':
                oid = ml.objid
                if ml.objid in abbrs:
                    oid = abbrs[ml.objid]
                elif ml.objid.upper() in abbrs:
                    oid = abbrs[ml.objid.upper()]
                elif 'P' + ml.objid in abbrs:
                    oid = abbrs['P' + ml.objid]
                elif not oid and (ml.label in names):
                    oid = names[ml.label]
                if oid != ml.objid:
                    ml.url = 'LanguageTable#cldf:' + oid
                if not oid:
                    return ml.label
            return ml

        res = CLDFMarkdownLink.replace(link_languages(text), repl)

        def repl(ml):
            if roots and ml.url.startswith('root-acd'):
                key = ml.label.strip().replace('&ast;', '')
                if key in roots:
                    ml.url = 'cf.csv#cldf:{}'.format(roots[key])
                    removal_marker = '__remove__' if '(' in ml.url else ''
                    if removal_marker:
                        assert ')' not in ml.url
                        return '{}{}'.format(ml, removal_marker)
                    return ml
                return ml.label
            return ml

        res = MarkdownLink.replace(res, repl).replace('__remove__)', '')
        assert '__remove__' not in res, res
        return res

    def cmd_makecldf(self, args):
        self.schema(args.writer.cldf)
        self.local_schema(args.writer.cldf)

        # Add sources
        args.writer.cldf.sources.add(*self.etc_dir.read_bib())

        # Add varieties
        # Update language metadata according to changes in etc/languages.tsv and Glottolog
        glangs = self.glottolog_cldf_languoids(
            '../../glottolog/glottolog-cldf', args.glottolog_version)
        for kw in self.languages:
            glang = glangs.get(kw['Glottocode'])
            if glang:
                if glang.cldf.latitude:
                    kw['Latitude'] = glang.cldf.latitude
                    kw['Longitude'] = glang.cldf.longitude
                kw['Glottolog_Name'] = glang.cldf.name
                kw['ISO639P3code'] = glang.cldf.iso639P3code
            kw['Source'] = kw['Source'].split(';') if kw['Source'] else []
            del kw['Location']
            del kw['Alias']
            del kw['ISOname']
            kw['Is_Proto'] = kw['Is_Proto'] == 'true'
            if kw['Abbr']:
                if kw['Abbr'] in PROTO_DESC:
                    kw['Description'] = PROTO_DESC[kw['Abbr']]
            args.writer.add_language(**kw)
        varieties = Varieties(args.writer)

        # Add the classification tree
        t = newick.loads(TREE.newick)[0]
        t.rename(**varieties.abbr2id)
        args.writer.objects['MediaTable'].append(dict(
            ID='tree',
            Name='Newick tree',
            Description='The tree structure of the reconstruction levels in ACD',
            Media_Type='text/x-nh',
            Download_URL=data_url(t.newick, 'text/x-nh'),
        ))
        args.writer.objects['TreeTable'].append(dict(
            ID='tree',
            Name='1',
            Description='The tree structure of the reconstruction levels in ACD',
            Tree_Is_Rooted='Yes',
            Tree_Type='summary',
            Media_ID='tree',
        ))

        # Add parameters
        meanings = {}  # We copy the meaning descriptions to forms.
        cldf = CLDFDataset.from_metadata(self.raw_dir / 'v1.2' / 'cldf-metadata.json')
        for row in cldf['ParameterTable']:
            meanings[row['ID']] = row['Name']
            args.writer.add_concept(**row)

        # Add forms
        glosses = {r['Form_ID_v1.2']: r for r in self.etc_dir.read_csv('glosses.csv', dicts=True)}
        forms = Forms()
        for row in cldf['FormTable']:
            row['Description'] = meanings[row['Parameter_ID']]
            if row['ID'] in glosses:
                fixed = glosses.pop(row['ID'])
                if fixed['Source']:
                    row['Source'] = fixed['Source'].split()
                row['Description'] = fixed['Gloss_Fixed']
            row['Description'] = self.fix_markdown(row['Description'])
            row['Value'] = fixed_form(row['Value'])
            row['Form'] = fixed_form(row['Form'])
            del row['Segments']
            del row['is_proto']
            del row['is_root']
            forms[row['ID']] = args.writer.add_form(**row)  # map old form ID to new object.
        assert not glosses, 'Not all incorrect glosses have been detected!'

        # Split items in CognatesetTable into etyma and cf sets
        # and add in the Dempwolff reconstructions for near and noise sets.
        cfids = set()  # We store the IDs of Cognatesets which were turned into cf sets.
        dempwolff_info = {
            (r['Category'], r['Set_ID']): r['Etymology']
            for r in self.etc_dir.read_csv('dempwolff_etymologies.csv', dicts=True)}
        roots = root2id(cldf)

        for row in cldf['CognatesetTable']:
            row['Name'] = fixed_form(row.pop('Form'))
            row['Source'] = [src.replace('[]', '') for src in row['Source']]
            row['Comment'] = self.fix_markdown(row['Comment'], roots=roots)
            cat = row.pop('Contribution_ID')
            if cat == 'Canonical':
                del [row['Proto_Language']]
                row['Initial'] = get_initial(row['Name'])
                args.writer.objects['etyma.csv'].append(row)
            else:
                assert not row.pop('Proto_Language')
                assert row['ID'].startswith(cat + '-')
                _, _, nid = row['ID'].partition('-')
                cfids.add(row['ID'])
                row['Category'] = cat.lower()
                row['Dempwolff_Etymology'] = dempwolff_info.pop((row['Category'], nid), None)
                args.writer.objects['cf.csv'].append(row)
        assert not dempwolff_info, 'Not all Dempwolff reconstructions could be assigned!'

        # Add cognate sets (and reconstructions as cognates)
        doublet_sets, disjunct_sets = {}, {}
        for row in self.etc_dir.read_csv('doublets_and_disjuncts.csv'):
            for id_ in row[2].split():
                (doublet_sets if row[0] == 'Doublet' else disjunct_sets)[id_] = row[1]
        pf2cs = {}
        # All reconstructions in the same subset belong to the same cognate set!
        for (eid, subset), rows in itertools.groupby(
            sorted(
                [r for r in cldf['protoforms.csv'] if not r['Inferred']],
                key=lambda r: (r['Cognateset_ID'], int(r['Subset'] or 0))),
            lambda r: (r['Cognateset_ID'], r['Subset']),
        ):
            rows = list(rows)
            main = main_reconstruction(rows)
            comments = [r['Comment'] for r in rows if r['Comment']]
            assert len(comments) < 2
            csid = '{}{}'.format(eid, '_' + subset if subset else '')
            args.writer.objects['CognatesetTable'].append(dict(
                ID=csid,
                Name="{} {} '{}'".format(
                    forms.labbr(main['Form_ID'], varieties),
                    forms.form(main['Form_ID']),
                    forms.meaning(main['Form_ID'])),
                Etymon_ID=eid,
                Form_ID=forms.id(main['Form_ID']),
                Comment=self.fix_markdown(comments.pop()) if comments else None,
                Is_Main_Entry=subset is None or (int(subset) == 1),
            ))
            for row in rows:
                pf2cs[row['ID']] = csid
                args.writer.add_cognate(
                    ID=row['ID'],
                    Form_ID=forms.id(row['Form_ID']),
                    Cognateset_ID=csid,
                    Doublet_Comment=row['Doublet_Comment'],
                    Disjunct_Comment=row['Disjunct_Comment'],
                    Doublet_Set=doublet_sets.get(row['ID']),
                    Disjunct_Set=disjunct_sets.get(row['ID']),
                )

        # Add cognates and cf items:
        loans = set()
        cognates = collections.defaultdict(list)
        metathesis = {
            r['CID'] for r in self.etc_dir.read_csv('metathesis.tsv', dicts=True, delimiter='\t')}
        assimilation = {
            r['CID'] for r in self.etc_dir.read_csv('assimilation.tsv', dicts=True, delimiter='\t')}
        brax = {
            tuple(r) for i, r in
            enumerate(self.etc_dir.read_csv('brax.tsv', delimiter='\t')) if i and r}
        brax_forms = collections.defaultdict(list)
        for row in cldf['CognateTable']:
            if row['Cognateset_ID'] in cfids:
                cat, _, nid = row['Cognateset_ID'].partition('-')
                assert cat in ['Root', 'Noise', 'Near']
                args.writer.objects['cfitems.csv'].append(dict(
                    ID=row['ID'],
                    Cfset_ID=row['Cognateset_ID'],
                    Form_ID=forms.id(row['Form_ID']),
                ))
            else:
                eid = pf2cs[row['Reconstruction_ID']].split('_')[0]
                brax_key = (
                    eid,
                    forms.lname(row['Form_ID'], varieties).replace(' ', '_'),
                    forms.form(row['Form_ID']))
                if brax_key in brax:
                    brax.remove(brax_key)
                    brax_forms[pf2cs[row['Reconstruction_ID']]].append(row['Form_ID'])
                else:
                    cognates[forms.id(row['Form_ID'])].append(row['Reconstruction_ID'])
                    args.writer.add_cognate(
                        ID=row['ID'],
                        Form_ID=forms.id(row['Form_ID']),
                        Metathesis=row['ID'] in metathesis,
                        Assimilation=row['ID'] in assimilation,
                        Cognateset_ID=pf2cs[row['Reconstruction_ID']],
                    )
                    if row['ID'] in assimilation:
                        assimilation.remove(row['ID'])
                    if row['ID'] in metathesis:
                        metathesis.remove(row['ID'])
        assert not metathesis, metathesis
        assert not assimilation, assimilation
        assert not brax, 'Not all brax items matched: {}'.format(brax)

        # Add groups of bracketed forms as cf items:
        for csid, fids in brax_forms.items():
            cfid = csid + '-also'
            args.writer.objects['cf.csv'].append(dict(
                ID=cfid, Name='Also', Category='also', Cognateset_ID=csid))
            for fid in fids:
                args.writer.objects['cfitems.csv'].append(dict(
                    ID='{}-{}'.format(cfid, fid), Cfset_ID=cfid, Form_ID=forms.id(fid)))

        # Turn loansets into cf sets
        for row in cldf['loansets.csv']:
            row['Name'] = row.pop('Gloss')
            row['Category'] = 'loan'
            del(row['Contribution_ID'])
            row['Comment'] = self.fix_markdown(row['Comment'])
            assert '__language_' not in (row['Comment'] or '')
            args.writer.objects['cf.csv'].append(row)

        # Add borrowings
        for row in cldf['BorrowingTable']:
            row['Cfset_ID'] = row.pop('Loanset_ID')
            args.writer.objects['BorrowingTable'].append(row)
            loans.add(row['Target_Form_ID'])

        for form in args.writer.objects['FormTable']:
            if form['ID'] in loans:
                form['Loan'] = True
            if form['ID'] in cognates:
                form['Cognacy'] = ' '.join(sorted(cognates[form['ID']], key=int))

    def local_schema(self, cldf):
        cldf.add_table(
            'etyma.csv',
            {
                'name': 'ID',
                'dc:description':
                    'A numeric identifier for the etymon. For etyma present in the legacy online '
                    'version of ACD this number will match the cognate set number assigned then.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
            {
                'name': 'Name',
                'dc:description': 'The core reconstruction uniting the cognate sets of the etymon.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name'},
            {
                'name': 'Initial',
                'datatype': {'base': 'string', 'format': '|'.join(GRAPHEMES)}},
            {
                'name': 'Description',
                'dc:description': 'The reconstructed meaning of the etymon.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description'},
            {
                'name': 'Comment',
                "dc:conformsTo": "CLDF Markdown",
                "dc:format": "text/markdown",
                'dc:description':
                    'Some notes are several lines, while others are a page or more. Notes are used '
                    'for a variety of purposes. Among the most common are to report other forms '
                    'that show a likely historical connection with those cited in the main '
                    'comparison, but which exhibit irregularities other than the usual sporadic '
                    'assimilation or metathesis, and so raise more serious questions about '
                    'comparability, as in entry (2) above; to discuss details of the reconstructed '
                    'gloss; and to note the occurrence of monosyllabic “roots” or submorphemic '
                    'sound-meaning correlations in reconstructed morphemes.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#comment'},
            {
                'name': 'Source',
                'separator': ';',
                'dc:description': 'Sources mentioned in the comment describing the etymon.',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
        )
        # We need to mark the "main" reconstruction per etymon!
        """
        The ACD differs from almost all other comparative dictionaries by including reconstructions 
        of affixed forms, reduplications, and compounds wherever there is comparative evidence to 
        support them. [...] the main entry is followed by [...] subentries.
        """

        cldf.add_columns(
            'CognatesetTable',
            'Etymon_ID',
            {'name': 'Is_Main_Entry', 'datatype': 'boolean'},
        )
        cldf.add_foreign_key('CognatesetTable', 'Etymon_ID', 'etyma.csv', 'ID')

        for key, value in DESCRIPTIONS.items():
            cldf[key].common_props['dc:description'] = value

        cldf.add_columns(
            'cf.csv',
            {
                'name': 'Dempwolff_Etymology',
                'dc:description':
                    'A corresponding (unsupported) reconstruction posited in Dempwolff 1938.',
            })
        cldf.add_foreign_key('LanguageTable', 'Dialect_Of', 'LanguageTable', 'ID')

        rlevels = [n.name for n in TREE.walk()]
        cldf['LanguageTable', 'Group'].datatype = Datatype.fromvalue({
            'base': 'string',
            'format': '|'.join(rlevels),
            'dc:description':
                'Each language is assigned to one of the nine reconstruction levels (or Form. '
                'or PAN).',
        })
        cldf.add_component('TreeTable')
        cldf.add_component('MediaTable')
