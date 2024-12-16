"""
Display an etymon, i.e. a cognate set, including subsets.
"""
import itertools
import collections

from bs4 import BeautifulSoup
from markdown import markdown
from termcolor import colored
import newick
from pycldf.trees import TreeTable

from lexibank_acd import Dataset


def register(parser):
    parser.add_argument('etymon')
    parser.add_argument('--with-reconstruction-tree', action='store_true', default=False)


def run(args):
    cldf = Dataset().cldf_reader()
    for tree in TreeTable(cldf):
        tree = tree.newick()
        break

    langs = {l['ID']: l for l in cldf['LanguageTable']}  # Lookup for language metadata.
    forms = {l['ID']: l for l in cldf['FormTable']}  # Lookup for form metadata.

    rlevels = [langs[n.name]['Abbr'] for n in tree.walk()]

    for row in cldf['etyma.csv']:  # Find the referenced etymon.
        if (row['Name'].replace('*', '') == args.etymon.replace('*', '')) or (row['ID'] == args.etymon):
            ety = row
            break
    else:
        raise ValueError('Unknown etymon: {}'.format(args.etymon))

    # Aggregate the subsets linked to the etymon:
    css = [
        (row, [], row['Is_Main_Entry'])
        for row in cldf['CognatesetTable'] if row['Etymon_ID'] == ety['ID']]
    for row in cldf['CognateTable']:
        for cs, cogs, _ in css:
            if row['Cognateset_ID'] == cs['ID']:
                cogs.append(row)

    # Aggregate the linked cf sets:
    cfsets = collections.defaultdict(list)
    for row in cldf['cf.csv']:
        if row['Cognateset_ID']:
            cfsets[row['Cognateset_ID']].append(row)

    lines = []
    pfs = {node.name: '' for node in tree.walk()}
    for i, (cs, cogs, main) in enumerate(css):  # Display each subset.
        if i > 0:
            lines.append('---')
        cogs = [(cog, forms[cog['Form_ID']], langs[forms[cog['Form_ID']]['Language_ID']]) for cog in cogs]
        cogs = sorted(
            cogs,
            key=lambda c: (
                rlevels.index(c[2]['Group']),
                0 if c[2]['Abbr'] in rlevels else 1,
                0 if c[2]['Is_Proto'] else 1,
                # sort langs within group: North to South, except Oceanic: West to East
                -(c[2]['Latitude'] or 0) if c[2]['Group'] != 'POC' else abs(c[2]['Longitude'] or 0),
            ))

        for level, cognates in itertools.groupby(cogs, lambda c: c[2]['Group']):
            group = None
            for cog, form, lang in cognates:
                if not lang['Abbr']:
                    if lang['Group'] != group:
                        lines.append('  ' + fmt_group(lang['Group']))
                        group = lang['Group']
                if lang['Abbr'] == level:
                    if main:
                        pfs[lang['ID']] = form['Value']
                    cmt = ''
                    if cog['Doublet_Comment']:
                        cmt = '[doublet: {}]'.format(cog['Doublet_Comment'])
                    if cog['Disjunct_Comment']:
                        cmt = '[disjunct: {}]'.format(cog['Disjunct_Comment'])
                    lines.append('{} {} {} {}'.format(lang['Abbr'], fmt_protoform(form['Value']), fmt_meaning(form['Description']), cmt))
                else:
                    sound_change = ''
                    if cog['Metathesis']:
                        sound_change += 'ᴹ'
                    if cog['Assimilation']:
                        sound_change += 'ᴬ'
                    lines.append('\t{}\t{}{}\t{}'.format(fmt_lang(lang['Name']), fmt_form(form['Value']), sound_change, fmt_meaning(form['Description'])))

        for cfset in cfsets.get(cs['ID'], []):
            lines.append('Also')
            for item in cldf['cfitems.csv']:
                if item['Cfset_ID'] == cfset['ID']:
                    form = forms[item['Form_ID']]
                    lang = langs[form['Language_ID']]
                    lines.append('\t{}\t{}\t{}'.format(fmt_lang( lang['Name']), fmt_form(form['Value']), fmt_meaning(form['Description'])))

        if cs['Comment']:
            lines.append('\nNOTE: ' + fmt_comment(cs['Comment']))


    if ety['Comment']:
        lines.append('\nNOTE: ' + fmt_comment(ety['Comment']))

    if args.with_reconstruction_tree:
        t = newick.loads(tree.newick)[0]
        t.rename(auto_quote=True, **pfs)
        lines = [t.ascii_art()] + lines
    print('\n'.join(lines))


def fmt_form(s):
    return colored(s, 'blue')


def fmt_protoform(s):
    return colored(s, 'red')


def fmt_meaning(s):
    return '‘{}’'.format(fmt_comment(s))


def fmt_lang(s):
    return colored(s, 'light_green')


def fmt_group(s):
    if s.startswith('P'):
        s = s[1:]
    return colored(s, 'green')


def fmt_comment(t):
    """
    '<p>Also <a href="LanguageTable#cldf:279">Ilokano</a> <em>kúrad</em> ‘contagious affection of the skin characterized by the appearance of discolored whitish patches covered with vesicles or powdery scales, and at times itching greatly; a kind of tetter or ringworm’, <a href="LanguageTable#cldf:18314">Karo Batak</a> <em>kudil</em> ‘scabies’, <em>kudil-en</em> ‘suffer from scabies’, <a href="LanguageTable#cldf:285">Javanese</a> <em>kuḍas</em> ‘ringworm’, <a href="LanguageTable#cldf:404">Sasak</a> <em>kurék</em> ‘scabies, itch’.</p>'
    """
    bs = BeautifulSoup(markdown(t), 'lxml')
    for a in bs.find_all('a'):
        if a['href'].startswith('LanguageTable'):
            a.replace_with(fmt_lang(a.text))
        if a['href'].startswith('Source'):
            a.replace_with(colored(a.text, attrs=['underline']))
    for a in bs.find_all('em'):
        a.replace_with(fmt_form(a.text))
    return bs.get_text().replace('&ast;', '*')
