"""

"""
from pylexibank.cldf import LexibankWriter
from clldutils.clilib import PathType
from csvw.dsv import reader

from lexibank_acd import Dataset, hash


class UpdateWriter(LexibankWriter):
    def __init__(self, cldf_spec, args, dataset):
        super().__init__(cldf_spec=cldf_spec, args=args, dataset=dataset, clean=False)

    def __enter__(self):
        cldf = self.dataset.cldf_reader()
        super().__enter__()

        self.dataset.add_schema(self._cldf)
        for table in cldf.tables:
            try:
                tt = cldf.get_tabletype(table)
            except ValueError:
                tt = None
            for obj in table:
                if tt and tt in self._obj_index:
                    self._obj_index[tt or str(table.url)].add(obj['ID'])
                self.objects[tt or str(table.url)].append(obj)
        return self


def register(parser):
    #
    # FIXME: must register catalogs!
    #
    parser.add_argument('datadir', type=PathType(type='dir'))


def run(args):
    # read the old cldf data
    # add
    # write the cldf data
    ds = Dataset()
    data = {}
    for name in ['forms', 'metadata']:
        p = args.datadir.joinpath('{}.tsv'.format(name))
        assert p.exists()
        data[name] = list(reader(p, delimiter='\t', dicts=True))
    with UpdateWriter(ds.cldf_specs(), args, ds) as writer:
        assert len(data['metadata']) == 1
        for lang in data['metadata']:
            lid = str(max(int(i) for i in writer._obj_index['LanguageTable']) + 1)
            """
    glottocode	name	group	ISO639P3code	isoname	location	Alias	source	lon	lat
    puna1274	Merap	wmp	puc	Punan Merap	Indonesia (Kalimantan)	Punan Merap, Mpraa	Smith 2017 merap	116.454	3.085
            """
            writer.add_language(
                ID=lid,
                Name=lang['name'],
            )
            break
        for form in data['forms']:
            cid = hash(form['merap gloss'])
            if cid not in writer._obj_index['ParameterTable']:
                writer.add_concept(
                    ID=cid,
                    Name=form['merap gloss'],
                )

            for lexeme in writer.add_forms_from_value(
                Language_ID=lid,
                Parameter_ID=cid,
                Value=form['Merap'],
            ):
                writer.add_cognate(
                    Form_ID=lexeme['ID'],
                    Form=lexeme,
                    Reconstruction_ID=str(sid),
                    Cognateset_ID=str(etymon['id']),
                    Proto_Language=pl,
                )
