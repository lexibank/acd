import re
import hashlib
import itertools
import pathlib
import collections

import attr
import newick
import pylexibank
from clldutils import jsonlib
from clldutils.misc import slug
from csvw.dsv import UnicodeWriter, reader

from acdparser import RECONCSTRUCTIONS
from acdparser.parser import RootParser, LoanParser
from acdparser import updates

TREE = newick.loads('(Formosan,((PPh)PWMP,(PCMP,(PSHWNG,POC)PEMP)PCEMP)PMP)PAN;')[0]


def infer_protoforms(sets):
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
                    # tree; thus we exlude all descendants of this nde from the search:
                    excluded = excluded.union(descendants[n.name])
                    continue

                if any(pl in attested for pl in descendants[n.name]):
                    # Reflexes are attested for a language that descended from this proto-language
                    yield s['id'], n.name, s['key'], s['gloss']


@attr.s
class Etymon(pylexibank.Cognate):
    Proto_Language = attr.ib(default=None)
    Reconstruction_ID = attr.ib(default=None)
    #
    # FIXME: bracketed
    #

@attr.s
class Form(pylexibank.Lexeme):
    is_root = attr.ib(default=False, metadata=dict(datatype='boolean'))
    is_proto = attr.ib(default=False, metadata=dict(datatype='boolean'))


@attr.s
class Variety(pylexibank.Language):
    ISOname = attr.ib(default=None)
    Group = attr.ib(default=None)
    Location = attr.ib(default=None)
    Alias = attr.ib(default=None)
    Source = attr.ib(default=None)
    is_proto = attr.ib(default=False, metadata=dict(datatype='boolean'))
    Dialect_Of = attr.ib(default=None)


def hash(s):
    return hashlib.md5(slug(s).encode('utf8')).hexdigest()


class Dataset(pylexibank.Dataset):
    dir = pathlib.Path(__file__).parent
    id = "acd"

    lexeme_class = Form
    cognate_class = Etymon
    language_class = Variety

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=('?', '-'),  # characters that denote missing data.
        strip_inside_brackets=True   # do you want data removed in brackets or not?
    )

    def cmd_download(self, args):
        from acdparser import parse, JsonEncoder

        res = parse(self.raw_dir)
        sources, langs, cogs, loans, nsets, nearsets, roots = res
        jsonlib.dump(sources, self.raw_dir / 'sources.json', cls=JsonEncoder)
        jsonlib.dump(langs, self.raw_dir / 'languages.json', cls=JsonEncoder)
        jsonlib.dump(cogs, self.raw_dir / 'cognates.json', cls=JsonEncoder)
        jsonlib.dump(loans, self.raw_dir / 'borrowings.json', cls=JsonEncoder)
        jsonlib.dump(nsets, self.raw_dir / 'noise.json', cls=JsonEncoder)
        jsonlib.dump(nearsets, self.raw_dir / 'near.json', cls=JsonEncoder)
        jsonlib.dump(roots, self.raw_dir / 'root.json', cls=JsonEncoder)

    def _schema(self, args):
        args.writer.cldf.add_component('ContributionTable')

        args.writer.cldf.add_component(
            'CognatesetTable',
            'Form',
            'Comment',
            'Proto_Language',
            'Contribution_ID',
        )
        args.writer.cldf.add_foreign_key('CognatesetTable', 'Contribution_ID', 'ContributionTable', 'ID')

        t = args.writer.cldf.add_table(
            'loansets.csv',
            'ID',
            'Gloss',
            'Dempwolff_Etymology', #-> in Borrowings!? (Dempwolff: *tarima ‘receive, accept’)
            'Contribution_ID',
            'Comment',
        )
        t.tableSchema.primaryKey = ['ID']
        args.writer.cldf.add_component('BorrowingTable', 'Loanset_ID')
        args.writer.cldf.add_foreign_key('loansets.csv', 'Contribution_ID', 'ContributionTable', 'ID')
        args.writer.cldf.add_foreign_key('BorrowingTable', 'Loanset_ID', 'loansets.csv', 'ID')

        t = args.writer.cldf.add_table(
            'protoforms.csv',
            'ID',
            'Cognateset_ID',
            'Form_ID',
            'Subset',
            'Proto_Language',
            'Comment',
            {'name': 'Inferred', 'datatype': 'boolean'},
            'Doublet_Comment',
            'Disjunct_Comment',
            {
                'name': 'Doublets',
                'separator': ' ',
                'dc:description': "variants that are independently supported by the comparative evidence",
            },
            {
                'name': 'Disjuncts',
                'separator': ' ',
                'dc:description': "",
            },
        )
        t.tableSchema.primaryKey = ['ID']
        #t.common_props['dc:description'] = ""
        args.writer.cldf.add_foreign_key('protoforms.csv', 'Form_ID', 'FormTable', 'ID')
        args.writer.cldf.add_foreign_key('protoforms.csv', 'Cognateset_ID', 'CognatesetTable', 'ID')
        args.writer.cldf.add_foreign_key('protoforms.csv', 'Doublets', 'protoforms.csv', 'ID')
        args.writer.cldf.add_foreign_key('protoforms.csv', 'Disjuncts', 'protoforms.csv', 'ID')

    def cmd_makecldf(self, args):
        self._schema(args)

        args.writer.add_languages()
        languages = args.writer.objects['LanguageTable']
        l2id = {l['Name']: l['ID'] for l in languages}
        for l in languages:
            if l['Group'].startswith('P'):
                l2id[l['Group'].upper()] = l['ID']
            if '(' in l['Name']:
                # Sambal (Botolan) -> Botolan Sambal
                comps = l['Name'].replace(')', '').split('(', 1)
                l2id['{} {}'.format(comps[1].strip(), comps[0].strip())] = l['ID']
        langs = jsonlib.load(self.raw_dir / 'languages.json')
        for l in args.writer.objects['LanguageTable']:
            l['is_proto'] = l['Name'].startswith('Proto-')
            l['Dialect_Of'] = langs.get(l['ID'], {}).get('parent_language')

        lid_by_group = {l['Group']: l['ID'] for l in args.writer.objects['LanguageTable']}
        assert all(k in lid_by_group for k in RECONCSTRUCTIONS)

        args.writer.objects['ContributionTable'].append(dict(
            ID='Canonical',
            Name='Canonical comparisons',
            Description='Comparisons with regular sound correspondences and close semantics. If '
                        'there are additional forms that are strikingly similar but irregular, or '
                        'that show strong semantic divergence, these are are added in a note. '
                        'Every attempt is made to keep the comparison proper free from problems.',
        ))
        args.writer.objects['ContributionTable'].append(dict(
            ID='Root',
            Name='Roots',
            Description=RootParser.__doc__,
        ))
        args.writer.objects['ContributionTable'].append(dict(
            ID='Loan',
            Name='Loans',
            Description=LoanParser.__doc__,
        ))
        args.writer.objects['ContributionTable'].append(dict(
            ID='Near',
            Name='Near comparisons',
            Description='Forms that are strikingly similar but irregular, and which cannot be '
                        'included in a note to an established reconstruction. Stated differently, '
                        'these are forms that appear to be historically related, but do not yet '
                        'permit a reconstruction.',
        ))
        args.writer.objects['ContributionTable'].append(dict(
            ID='Noise',
            Name='Noise (look-alikes)',
            Description="""Given the number of languages being compared and the number of forms in 
many of the sources, forms that resemble one another in shape and meaning by chance will not be 
uncommon, and the decision as to whether a comparison that appears good is a product of chance 
must be based on criteria such as

- how general the semantic category of the form is (e.g. phonologically corresponding forms 
  meaning ‘cut’ are less diagnostic of relationship than phonologically corresponding forms for 
  particular types of cutting),
- how richly attested the form is (if it is found in just two witnesses the likelihood that it is 
  a product of chance is greatly increased),
- there is already a well-established reconstruction for the same meaning.
""",
        ))

        links = collections.defaultdict(lambda: collections.defaultdict(set))
        concepts, etyma = set(), collections.defaultdict(set)
        for language in jsonlib.load(self.raw_dir / 'languages.json').values():
            for form in language['forms']:
                concept = form['gloss']['plain']
                cid = hash(concept)
                if cid not in concepts:
                    args.writer.add_concept(
                        ID=cid,
                        Name=concept,
                        #Description=form['gloss']['markdown'],
                    )
                    concepts.add(cid)

                for lexeme in args.writer.add_forms_from_value(
                    Language_ID=language['id'],
                    Parameter_ID=cid,
                    Value=form['form'],
                    is_root=form['is_root'],
                    is_proto=language['is_proto'],
                    #Source=[row['Source']],
                ):
                    for i in form['sets']:
                        links[i[0]][int(i[1])].add((lexeme['ID'], lexeme['Form']))

        etyma = jsonlib.load(self.raw_dir / 'cognates.json')
        setids = list(itertools.chain(*[[s['id'] for s in e['sets']] for e in etyma]))
        for etymon in etyma:
            for i, s in enumerate(etymon['sets']):
                sid, pl = s['id'], s['proto_language']
                if i == 0:
                    args.writer.objects['CognatesetTable'].append(dict(
                        ID=str(etymon['id']),
                        Contribution_ID='Canonical',
                        Form=s['key'],
                        Description=s['gloss'],
                        Proto_Language=pl,
                        Comment=etymon['note']['markdown'] if etymon['note'] else None,
                    ))
                cid = hash(s['gloss'])
                if cid not in concepts:
                    args.writer.add_concept(
                        ID=cid,
                        Name=s['gloss'],
                        #Description=form['gloss']['markdown'],
                    )
                    concepts.add(cid)
                fid = 'protoform-{}'.format(sid)
                args.writer.objects['FormTable'].append(dict(
                    ID=fid,
                    Language_ID=lid_by_group[s['proto_language']],
                    Parameter_ID=cid,
                    Value=s['key'],
                    Form=s['key'].replace('*', ''),
                    is_proto=True,
                ))
                args.writer.objects['protoforms.csv'].append(dict(
                    ID=str(sid),
                    Form_ID=fid,
                    Proto_Language=pl,
                    Cognateset_ID=str(etymon['id']),
                    Comment=s['note']['markdown'] if s['note'] else None,
                    Subset=s['subset'],
                    Inferred=False,
                    Doublet_Comment=s['doublet_text'],
                    Disjunct_Comment=s['disjunct_text'],
                    Doublets=[str(k[1][1]) for k in s['doublets'] if k[1][0] in ['s', 'f'] and int(k[1][1]) in setids],
                    Disjuncts=[str(k[1][1]) for k in s['disjuncts'] if k[1][0] in ['s', 'f'] and int(k[1][1]) in setids],
                ))
                for t in ['s', 'f']:
                    for fid, form in links[t].get(sid, []):
                        args.writer.add_cognate(
                            Form_ID=fid,
                            Form=form,
                            Reconstruction_ID=str(sid),
                            Cognateset_ID=str(etymon['id']),
                            Proto_Language=pl,
                        )
            for _, sets in itertools.groupby(etymon['sets'], lambda s: s['subset']):
                for sid, plg, form, gloss in infer_protoforms(list(sets)):
                    fid = 'protoform-{}-{}'.format(sid, plg)
                    args.writer.objects['FormTable'].append(dict(
                        ID=fid,
                        Language_ID=lid_by_group[plg],
                        Parameter_ID=hash(gloss),
                        Value=form,
                        Form=form.replace('*', ''),
                        is_proto=True,
                    ))
                    args.writer.objects['protoforms.csv'].append(dict(
                        ID='{}-{}'.format(sid, plg),
                        Cognateset_ID=str(etymon['id']),
                        Form_ID=fid,
                        Proto_Language=plg,
                        Inferred=True,
                    ))
        for s in jsonlib.load(self.raw_dir / 'root.json'):
            sid = s['id']
            args.writer.objects['CognatesetTable'].append(dict(
                ID='{}-{}'.format('Root', sid),
                Contribution_ID='Root',
                Form=s['key'],
                Description=s['gloss'],
                Comment=s['note']['markdown'] if s['note'] else None,
            ))

            for fid, form in links['r'].get(sid, []):
                args.writer.add_cognate(
                    Form_ID=fid,
                    Form=form,
                    Cognateset_ID='{}-{}'.format('Root', sid),
                )
        for d, cid, lcat in [('near.json', 'Near', 'near'), ('noise.json', 'Noise', 'n')]:
            for s in jsonlib.load(self.raw_dir / d):
                sid = s['id']
                args.writer.objects['CognatesetTable'].append(dict(
                    ID='{}-{}'.format(cid, sid),
                    Contribution_ID=cid,
                    Description=s['gloss'],
                    Comment=s['note']['markdown'] if s['note'] else None,
                ))
                for fid, form in links[lcat].get(sid, []):
                    args.writer.add_cognate(
                        Form_ID=fid,
                        Form=form,
                        Reconstruction_ID=str(sid),
                        Cognateset_ID='{}-{}'.format(cid, sid),
                    )

        def de(s):
            if s.startswith('(Dempwolff'):
                s = re.sub(r'\(Dempwolff:\s*', '', s)
                if s.endswith(')'):
                    s = s[:-1].strip()
                return s

        bid = 0
        for s in jsonlib.load(self.raw_dir / 'borrowings.json'):
            sid = s['id']
            args.writer.objects['loansets.csv'].append(dict(
                ID='{}'.format(sid),
                Contribution_ID='Loan',
                Gloss=s['gloss'],
                Dempwolff_Etymology=de(s['loanform']) if s['loanform'] else None,
                Comment=s['note']['markdown'] if s['note'] else None,
            ))
            for fid, form in links['lo'].get(sid, []):
                bid += 1
                args.writer.objects['BorrowingTable'].append(dict(
                    ID=str(bid),
                    Target_Form_ID=fid,
                    #Form=form,
                    #Reconstruction_ID=str(sid),
                    Loanset_ID='{}'.format(sid),
                ))

        max_eid = 40000
        max_pfid = 20000
        forms_by_lgid = collections.defaultdict(dict)
        for f in args.writer.objects['FormTable']:
            forms_by_lgid[f['Language_ID']][f['Form']] = f['ID']

        for p in sorted(self.raw_dir.joinpath('updates').glob('*.odt'), key=lambda p_: p_.stem):
            for etymon, forms, note in updates.parse(p):
                assert etymon[0].upper() in l2id, str(etymon)
                nf = []
                for group, lg, a, b in forms:
                    if lg not in l2id:
                        if '(' in lg:
                            lg = '{} {}'.format(
                                lg.split('(')[1].replace(')', '').strip(), lg.split('(')[0].strip())
                    #assert group in l2id, group
                    assert lg in l2id, lg
                    nf.append([group, lg, a, b])
                forms = nf
                #sid, pl = s['id'], s['proto_language']
                max_eid += 1
                args.writer.objects['CognatesetTable'].append(dict(
                    ID=str(max_eid),
                    Contribution_ID='Canonical',
                    Form=etymon[1],
                    Description=etymon[2],
                    Proto_Language=etymon[0],
                    Comment=note,
                ))
                cid = hash(etymon[2])
                if cid not in concepts:
                    args.writer.add_concept(
                        ID=cid,
                        Name=etymon[2],
                        #Description=form['gloss']['markdown'],
                    )
                    concepts.add(cid)
                max_pfid += 1
                fid = 'protoform-{}'.format(max_pfid)
                args.writer.objects['FormTable'].append(dict(
                    ID=fid,
                    Language_ID=l2id[etymon[0]],
                    Parameter_ID=cid,
                    Value=etymon[1],
                    Form=etymon[1].replace('*', ''),
                    is_proto=True,
                ))
                args.writer.objects['protoforms.csv'].append(dict(
                    ID=str(max_pfid),
                    Form_ID=fid,
                    Proto_Language=etymon[0],
                    Cognateset_ID=str(max_eid),
                    Comment=None,
                    Subset=1,
                    Inferred=False,
                ))
                for group, lg, form, gloss in forms:
                    cid = hash(gloss)
                    if cid not in concepts:
                        args.writer.add_concept(ID=cid, Name=gloss)
                        concepts.add(cid)
                    form_id = forms_by_lgid[l2id[lg]].get(form)
                    if not form_id:
                        for lexeme in args.writer.add_forms_from_value(
                            Language_ID=l2id[lg],
                            Parameter_ID=cid,
                            Value=form,
                        ):
                            form_id = lexeme['ID']
                            break
                    #Source=[row['Source']],

                    args.writer.add_cognate(
                            Form_ID=form_id,
                            Form=form,
                            Reconstruction_ID=str(max_pfid),
                            Cognateset_ID=str(max_eid),
                            Proto_Language=etymon[0],
                    )
                #
                # FIXME: infer reconstructions!
                #