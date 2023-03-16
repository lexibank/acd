import hashlib
import pathlib
import collections

import attr
import newick
import pylexibank
from clldutils.misc import slug
from pycldf import Dataset as CLDFDataset
from csvw.dsv import reader

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
    Source = attr.ib(
        default=None,
        metadata=dict(propertyUrl='http://cldf.clld.org/v1.0/terms.rdf#source', separator=';')
    )
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
        pass

    def add_schema(self, cldf):
        cldf.add_component('ContributionTable')

        cldf.add_component(
            'CognatesetTable',
            'Form',
            'Comment',
            'Proto_Language',
            'Contribution_ID',
            #{"name": "Source", "separator": ";", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source"},
        )
        cldf.add_foreign_key('CognatesetTable', 'Contribution_ID', 'ContributionTable', 'ID')

        t = cldf.add_table(
            'loansets.csv',
            'ID',
            'Gloss',
            'Dempwolff_Etymology', #-> in Borrowings!? (Dempwolff: *tarima ‘receive, accept’)
            'Contribution_ID',
            'Comment',
        )
        t.tableSchema.primaryKey = ['ID']
        cldf.add_component('BorrowingTable', 'Loanset_ID')
        cldf.add_foreign_key('loansets.csv', 'Contribution_ID', 'ContributionTable', 'ID')
        cldf.add_foreign_key('BorrowingTable', 'Loanset_ID', 'loansets.csv', 'ID')

        t = cldf.add_table(
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
        cldf.add_foreign_key('protoforms.csv', 'Form_ID', 'FormTable', 'ID')
        cldf.add_foreign_key('protoforms.csv', 'Cognateset_ID', 'CognatesetTable', 'ID')
        cldf.add_foreign_key('protoforms.csv', 'Doublets', 'protoforms.csv', 'ID')
        cldf.add_foreign_key('protoforms.csv', 'Disjuncts', 'protoforms.csv', 'ID')
        cldf.add_foreign_key('CognateTable', 'Reconstruction_ID', 'protoforms.csv', 'ID')

    def cmd_makecldf(self, args):
        self.add_schema(args.writer.cldf)

        #
        # FIXME: Start out with data from v1.1:
        #
        bib = self.etc_dir.read_bib()
        args.writer.cldf.sources.add(*bib)
        bib = {e['key']: e.id for e in bib}
        update_bib(bib)

        cldf = CLDFDataset.from_metadata(self.raw_dir / 'v1.1' / 'cldf-metadata.json')
        for table in cldf.tables:
            try:
                tt = cldf.get_tabletype(table)
            except ValueError:
                tt = None
            for obj in table:
                if tt and tt in args.writer._obj_index:
                    args.writer._obj_index[tt or str(table.url)].add(obj['ID'])
                args.writer.objects[tt or str(table.url)].append(obj)

        forms_by_id = {f['ID']: f for f in cldf['FormTable']}
        protoforms = {}
        for pf in cldf['protoforms.csv']:
            if not pf['Inferred']:
                # FIXME: add Proto_Language to the key!?
                protoforms[forms_by_id[pf['Form_ID']]['Value']] = pf
                protoforms[pf['ID']] = pf

        #
        # FIXME: Update language metadata according to changes in etc/languages.tsv
        # **and** according to new Glottolog data!
        #for kw in self.languages:
        #    glang = args.glottolog.api.cached_languoids.get(kw['Glottocode'])
        #    if glang and glang.latitude:
        #        kw['Latitude'] = glang.latitude
        #        kw['Longitude'] = glang.longitude
        #        kw['Glottolog_Name'] = glang.name
        #        kw['ISO639P3code'] = glang.iso
        #    kw['Source'] = [bib[s.strip()] for s in kw['Source'].split(';') if s.strip() in bib]
        #    args.writer.objects['LanguageTable'].append(kw)
        #

        for d in self.raw_dir.joinpath('updates').iterdir():
            if not d.is_dir():
                continue
            data = {}
            for name in ['forms', 'metadata']:
                p = d.joinpath('{}.tsv'.format(name))
                assert p.exists()
                data[name] = list(reader(p, delimiter='\t', dicts=True))

            for lang in data['metadata']:
                lid = str(max(int(i) for i in args.writer._obj_index['LanguageTable']) + 1)
                args.writer.add_language(
                    ID=lid,
                    Name=lang['name'],
                    Group=lang['group'].upper(),
                    ISO639P3code=lang['ISO639P3code'],
                    Location=lang['location'],
                    Alias=lang['Alias'],
                    Source=[lang['source']],
                    Longitude=float(lang['lon']),
                    Latitude=float(lang['lat']),
                )
                break
            else:
                raise ValueError
            for form in data['forms']:
                cid = hash(form['merap gloss'] or form['gloss'])
                if cid not in args.writer._obj_index['ParameterTable']:
                    args.writer.add_concept(
                        ID=cid,
                        Name=form['merap gloss'],
                    )

                pf = protoforms[form['pfid']] if form['pfid'] else protoforms[form['reconstruction']]
                #
                # FIXME: add disambiguation markers!
                #
                if pf['Proto_Language'] != form['proto level'].upper():
                    print('{}: {} vs. {}'.format(form['reconstruction'], pf['Proto_Language'],
                                                 form['proto level'].upper()))
                    #
                    # FIXME: We might have to deepen the reconstruction level!?
                    #
                    pass
                for lexeme in args.writer.add_forms_from_value(
                    Language_ID=lid,
                    Parameter_ID=cid,
                    Value=form['Merap'],
                ):
                    args.writer.add_cognate(
                        lexeme=lexeme,
                        Reconstruction_ID=pf['ID'],
                        Cognateset_ID=pf['Cognateset_ID'],
                        Proto_Language=form['proto level'].upper(),
                    )

        return


def update_bib(bib):
    for k, v in {
        'Dempwolff 1938': 'Dempwolff 1934/38',
        'Dempwolff 1934-1938': 'Dempwolff 1934/38',
        'Dempwolff 1934-38': 'Dempwolff 1934/38',
        'Dempwolff 1939': 'Dempwolff 1934/38',
        'Dempwolff’s 1938': 'Dempwolff 1934/38',
        'Dempwolff 9138': 'Dempwolff 1934/38',
        'Dempwolfff 1938': 'Dempwolff 1934/38',
        'Dempwoff 1938': 'Dempwolff 1934/38',
        'Denmpwolff 1938': 'Dempwolff 1934/38',
        'Ross 1998': 'Osmond and Ross 1998',
        'Ross 2008': 'Ross, Pawley and Osmond 2008',
        'Ross 2003': 'Osmond, Pawley and Ross 2003',
        'Osmond 1998': 'Osmond and Ross 1998',
        'Verheijen 1967-70': 'Verheijen 1967/70',
        'Dempwolff 1924-1925': 'Dempwolff 1924/25',
        'Schulte 1971': 'Schulte Nordholt 1971',
        'Pratt 1893': 'Pratt 1984',
        'Lister-Turner 1954': 'Lister-Turner and Clark 1954',
        'Lister-Turner 1930': 'Lister-Turner and Clark 1930',
        'Li 2006': 'Li and Tsuchida 2006',
        'Van 1940': 'van der Veen 1940',
        'van 1940': 'van der Veen 1940',
        'Blust 1983-1984': 'Blust 1983/84',
        'Mintz 1985': 'Mintz and del Rosario Britanico 1985',
        'Starosta 1982': 'Starosta, Pawley and Reid 1982',
        'Verheijen 1967': 'Verheijen 1967/70',
        'Bender 2003': 'Bender et al. 2003',
        'Tsuchida 1987': 'Tsuchida, Yamada and Moriguchi 1987',
        'Fox 1993': 'Fox 1993a',
        'Warneck 1906': 'Warneck 1977',
        'Walsh 1966': 'Walsh and Biggs 1966',
        'Brown 1981': 'Brown and Witkowski 1981',
        'Tryon 1983': 'Tryon and Hackman 1983',
        '(Blust 1976': 'Blust 1976',
        'Pawley 1998': 'Pawley and Pawley 1998',
        'Pawley 2003': 'Pawley and Sayaba 2003',
    }.items():
        bib[k] = bib[v]
