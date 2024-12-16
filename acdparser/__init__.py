"""
The Austronesian Comparative Dictionary: A Work in Progress

    December 2013 Oceanic Linguistics 52(2): 493-523

DOI:10.1353/ol.2013.0016

https://www.researchgate.net/publication/265931196_The_Austronesian_Comparative_Dictionary_A_Work_in_Progress


Reconstructions in the ACD are assigned to any of nine distinct levels:
1. PAN (Proto-Austronesian),
2. PMP (Proto-Malayo-Polynesian),
3. PWMP (Proto-Western Malayo-Polynesian),
4. PPh (Proto-Philippines),
5. PCEMP, (Proto-Central-Eastern Malayo-Polynesian),
6. PCMP (Proto-Central Malayo-Polynesian),
7. PEMP (Proto-Eastern Malayo-Polynesian),
8. PSHWNG (Proto-South Halmahera-West New Guinea),
9. POC (Proto-Oceanic).

Subgroup labels that may require some explanation are:

MP : Malayo-Polynesian = all AN languages outside Taiwan.
WMP : Western Malayo-Polynesian = the AN languages of the Philippines, Borneo, the Malay peninsula
    and islands in peninsular Thailand and Burma, Sumatra, Java and its satellites, Bali, Lombok,
    western Sumbawa, Sulawesi, Palauan and Chamorro of western Micronesia, the seven or eight
    Chamic languages of mainland Southeast Asia and Hainan island, and Malagasy.
CEMP : Central-Eastern Malayo-Polynesian = CMP + EMP.
CMP : Central Malayo-Polynesian = the AN languages of the Lesser Sunda islands and the southern
    and central Moluccas of eastern Indonesia.
EMP : Eastern Malayo-Polynesian = SHWNG + OC.
SHWNG : South Halmahera-West New Guinea = the AN languages of southern Halmahera and the
    northern Bird’s Head peninsula of New Guinea.
OC : Oceanic = the roughly 460 AN languages of Melanesia, Micronesia and Polynesia except
    Palauan and Chamorro of western Micronesia.

Unlike these subgroup labels F (Formosan) is used as a cover term for the aboriginal languages of
Taiwan, which appear to belong to at least nine primary branches of the AN language family.
"""
import re
import json
import collections

from nameparser import HumanName

from acdparser.parser import *

SUBGROUPS = {
    'Form.': ('Formosan', ''),
    'MP': ('Malayo-Polynesian', 'all AN languages outside Taiwan'),
    'WMP': (
        'Western Malayo-Polynesian',
        'The Austronesian languages of the Philippines, Borneo, the Malay peninsula and islands in '
        'peninsular Thailand and Burma, Sumatra, Java and its satellites, Bali, Lombok, '
        'western Sumbawa, Sulawesi, Palauan and Chamorro of western Micronesia, the seven or '
        'eight Chamic languages of mainland Southeast Asia and Hainan island, and Malagasy.'),
    'CEMP': ('Central-Eastern Malayo-Polynesian', 'CMP + EMP'),
    'CMP': (
        'Central Malayo-Polynesian',
        'The Austronesain languages of the Lesser Sunda islands and the southern and central '
        'Moluccas of eastern Indonesia.'),
    'EMP': ('Eastern Malayo-Polynesian', 'SHWNG + OC'),
    'SHWNG': (
        'South Halmahera-West New Guinea',
        'The Austronesian languages of southern Halmahera and the northern Bird’s Head peninsula '
        'of New Guinea.'),
    'OC': (
        'Oceanic',
        'The roughly 460 Austronesian languages of Melanesia, Micronesia and Polynesia except '
        'Palauan and Chamorro of western Micronesia.')
}
#PMJ
#PSF

INVALID_LANGS = ['Kaniet (Thilenius)']
RECONCSTRUCTIONS = collections.OrderedDict([
    ('PAN', 'Proto-Austronesian'),
    ('PMP', 'Proto-Malayo-Polynesian'),
    ('PWMP', 'Proto-Western Malayo-Polynesian'),
    ('PPh', 'Proto-Philippines'),
    ('PCEMP', 'Proto-Central-Eastern Malayo-Polynesian'),
    ('PCMP', 'Proto-Central Malayo-Polynesian'),
    ('PEMP', 'Proto-Eastern Malayo-Polynesian'),
    ('PSHWNG', 'Proto-South Halmahera-West New Guinea'),
    ('POC', 'Proto-Oceanic')
])
TREE = '(Formosan,((PPh)PWMP,(PCMP,(PSHWNG,POC)PEMP)PCEMP)PMP)PAN;'


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, HumanName):
            return {'first': obj.first, 'middle': obj.middle, 'last': obj.last}
        return json.JSONEncoder.default(self, obj)


MISSED = collections.Counter()

def repl(languages_by_name, s):
    from fuzzywuzzy import fuzz

    res = []
    start = '__language__'
    while start in s:
        b, _, rem = s.partition(start)
        res.append(b)
        lname, rem = rem.split('__', maxsplit=1)
        lname = re.sub('\s+', ' ', lname.strip())
        if lname in languages_by_name:
            res.append('[{}](languages/{})'.format(lname, languages_by_name[lname]))
        else:
            for name, lid in languages_by_name.items():
                if fuzz.token_sort_ratio(name, lname) > 99.0:
                    res.append('[{}](languages/{})'.format(lname, lid))
                    break
            else:
                MISSED.update([lname])
                res.append(lname)
        s = rem
    res.append(s)
    return ''.join(res)


def parse(d):
    sources = {}
    for src in SourceParser(d):
        #if src.key in sources:
        #    raise ValueError(src.key)
        sources[src.key] = src

    refs = collections.Counter()
    langs = collections.OrderedDict()
    for lang in LanguageParser(d):
        refs.update([r for r, _ in lang.iter_refs()])
        langs[lang.id] = lang
    langs[19629].abbr = 'pwmc'
    assert len(langs) == len(set(l.name for l in langs.values())), 'duplicate language name'
    # So now, language names and ids are unique.
    lang_id_by_name = {l.name: lid for lid, l in langs.items()}

    loids = {l.id for l in LoanParser(d)}

    forms, linked_sets = set(), set()
    for l in langs.values():
        for form in l.forms:
            refs.update([r for r, _ in form.iter_refs()])
            forms.add((l.name, form.form))
            ns = set()
            for cat, no in form.sets:
                if cat == 'lo' and int(no) not in loids:
                    cat = 'near'
                if cat == 's' and no == '0' and form.gloss.plain == 'kind of shark':
                    cat, no = 'near', '29910'
                if cat in ['f', 's']:
                    linked_sets.add(int(no))
                ns.add((cat, no))
            form.sets = ns

    # We provide language forms for simple lookup:
    forms_by_lang = {}
    for l in langs.values():
        forms_by_lang[l.name] = {(f.form, f.gloss.plain): f for f in l.forms}
    for l in langs.values():
        # Proto forms are listed with abbreviated language name.
        if l.abbr and l.abbr not in forms_by_lang:
            forms_by_lang[l.abbr] = forms_by_lang[l.name]

    lang_id_by_name.update({plid: plid for plid in RECONCSTRUCTIONS})
    for gid, (gname, _) in SUBGROUPS.items():
        lang_id_by_name[gid] = gid
        lang_id_by_name[gname] = gid

    rootsets = []
    for s in RootParser(d):
        rootsets.append(s)
        refs.update([r for r, _ in s.iter_refs()])
        for f in s.forms:
            if f.language in [
                # FIXME: log these!?
                'Mb(T)', 'LgW', 'TYPE', 'LgL', 'LgS', 'SB', 'KADAYAN', '(??) *', 'SUB(S)', 'MOO',
            ]:
                continue
            assert f.language in forms_by_lang, f.language
            if (f.form, f.gloss.plain) not in forms_by_lang[f.language]:
                # FIXME: log these!
                #print('{}: {} {}'.format(f.language, f.form, f.gloss.plain))
                # Rembong: bunit peel the stalks of vegetables
                # Bungku: wita earth, land
                # Manggarai: wituk swaying the body, posturing
                pass
            else:
                form = forms_by_lang[f.language][f.form, f.gloss.plain]
                assert ('r', str(s.id)) in form.sets, '{} "{}": {} -- {}'.format(form.form, form.gloss.plain, form.sets, s.id)

    nearsets = []
    for near in NearParser(d):
        nearsets.append(near)
        refs.update([r for r, _ in near.iter_refs()])
        for f in near.forms:
            if f.language in [
                'PPn', 'Batangan'
            ]:
                # FIXME: log these!
                continue
            if (f.form, f.gloss.plain) not in forms_by_lang[f.language]:
                #print('{}: {} {}'.format(f.language, f.form, near.gloss))
                # Rarotongan: tino body
                # Malay: mə-ləcit fly off: fly off, squirt out
                # Palawano: deŋen river otter
                pass
            else:
                form = forms_by_lang[f.language][f.form, f.gloss.plain]
                assert ('near', str(near.id)) in form.sets, '{} "{}": {} -- {}'.format(form.form, form.gloss.plain, form.sets, near.id)

    noisesets = []
    for noise in NoiseParser(d):
        noisesets.append(noise)
        refs.update([r for r, _ in noise.iter_refs()])
        for f in noise.forms:
            if f.language in [
                'RHB', 'TND', 'LON', 'MUR',
            ]:
                # FIXME: log these!
                continue
            if (f.form, f.gloss.plain) not in forms_by_lang[f.language]:
                pass
                #print('{}: {} {}'.format(f.language, f.form, noise.gloss))
                # Thao: taqtaq adze something: chop, split, adze something
                # Paiwan: ŋasŋas be out of breath: pant, be out of breath
                # Tagalog: dúkit cut off
                # Ilokano: tata elder sibling: father, uncle, elder sibling
                # Malagasy: pelika fan: vibrate, fan
                # Balinese: tuli fast
                # Samoan: tafa-tafa flank: side, flank
                # Tagalog: kubót fold, wrinkle
                # Tagalog: labág free, on the loose
                # Old Javanese: a-sisib-an glide off, slide off
                # Old Javanese: taŋtaŋ grip, grasp
                # Tagalog: kugkog grate: to grate
                # Tagalog: sabád hindrance
                # Toba Batak: dahop join together
                # Tausug: kawin marry: wedding, to marry
                # Sinaugoro: gepa mat
                # Tagalog: kirót pain
                # Malagasy: dzuluka (a bar to prevent entrance pierce, skewer
                # Tagalog: lúlos slip off
                # Tagalog: layláy spread out
                # Ngaju Dayak: lawas stand open
                # Malay: lawas stand open
                # Tagalog: kaykay stand up
                # Paiwan: tjiptjip suck
                # Ilokano: kahút take with hand
                # Tagalog: pásaŋ wooden implement
            else:
                form = forms_by_lang[f.language][f.form, f.gloss.plain]
                assert ('n', str(noise.id)) in form.sets, '{} -- {}'.format(form.sets, noise.id)

    loans = []
    for loan in LoanParser(d):
        loans.append(loan)
        refs.update([r for r, _ in loan.iter_refs()])
        for f in loan.forms:
            if f.language in [
                'NGA', 'RNB', 'PCS', 'K-K', 'CRAM',
            ]:
                continue
            if (f.form, f.gloss.plain) not in forms_by_lang[f.language]:
                pass
                #print('{}: {} {}'.format(f.language, f.form, loan.gloss))
                # Bikol: mag-gúlpi all at once: sudden(ly), all at once
                # Ilokano: limós alms
                # Tae': tadi-i artificial cockspur
                # Agutaynen: láŋka Artocarpus: jackfruit Artocarpus spp.
                # Toba Batak: pisaŋ banana
                # Casiguran Dumagat: kahíl Bitter orange Seville orange: Citrus aurantium
                # Hanunóo: kahíl Bitter orange Seville orange: Citrus aurantium
                # Ilokano: Insík Chinese
                # Tagalog: Insík Chinese
                # Tagalog: sigih-an continue
                # Binukid: ka-piaŋ crippled, lame
                # Sundanese: gedoŋ bicara discussion: speak, discussion
                # Bontok: talóŋ eggplant
                # Casiguran Dumagat: búrupickled ipon fish: pickled fish
                # Pazeh: ʔa:kúŋ grandfather
                # Samoan: ʔava kava: Piper methysticum
                # Toba Batak: undaŋ law
                # Javanese: unḍaŋ law
                # Ilokano: líra lyre
                # Sundanese: tilam quilt mattress thin cover to sleep on
                # Maranao: talompaʔ ~ tarompaʔ sandal
                # Paiwan: ts<alʸ>ebak shoot
                # Malay: pandak ~ pendek short
                # Tagalog: tíbay sound: well-made structurally sound
                # Ibaloy: pison steamroller
                # Tboli: atis Sweetsop: Annona squamosa
                # Ilokano: kaʔiŋin swidden
                # Tagalog: kaʔiŋin swidden
                # Cebuano: kaʔiŋin swidden
                # Malay: pədaŋ sword
                # Hanunóo: kaládiʔ taro variety
                # Tagalog: tuksó temptation; to tempt
                # Bikol: ma-tipíd thrifty
                # Bikol: título title (to land)
                # Bontok: tabáko tobacco
                # Agutaynen: pabo turkey
                # Malay: pəñəŋat wasp
            else:
                form = forms_by_lang[f.language][f.form, f.gloss.plain]
                form.sets.add(('lo', str(loan.id)))
                form.is_loan = True

    # Now we cross-check the forms listed on the Words pages:
    for w in WordParser(d):
        if w.language in INVALID_LANGS:
            continue
        # All languages are recoginzed - either by name or by lowercase abbreviation:
        assert (w.language in forms_by_lang) or (w.language.lower() in forms_by_lang), w.language
        forms = forms_by_lang.get(w.language, forms_by_lang.get(w.language.lower()))
        # All forms are found among the forms listed on the language pages:
        assert (w.form, w.gloss.plain) in forms, '{}: "{}" {}'.format(w.language, w.form, w.gloss.plain)

    # Now check the Set pages:
    sets, etyma = set(), collections.defaultdict(set)
    cognates = list(EtymonParser(d))
    for e in cognates:
        if e.note:
            e.note.markdown = repl(lang_id_by_name, e.note.markdown)
        refs.update([r for r, _ in e.iter_refs()])
        for s in e.sets:
            if s.note:
                s.note.markdown = repl(lang_id_by_name, s.note.markdown)
            refs.update([r for r, _ in s.iter_refs()])
            etyma[e.id].add(s.id)
            if s.id in sets:
                raise ValueError(s.id)
            sets.add(s.id)
            for f in s.forms:
                if f.language in INVALID_LANGS:
                    continue
                assert f.language in forms_by_lang, f.language
                form = f.form
                if f.note:
                    form = '{} ({})'.format(form, f.note)
                assert (form, f.gloss.plain) in forms_by_lang[f.language], '{}: "{}" {}'.format(f.language, form, f.gloss.plain)
                lform = forms_by_lang[f.language][(form, f.gloss.plain)]
                assert ('s', str(s.id)) in lform.sets or (('f', str(s.id)) in lform.sets), '{} -- {}'.format(lform.sets, s.id)
                lform.form = f.form
                lform.note = f.note
                lform.is_root = f.is_root
                lform.ass = f.ass
                lform.met = f.met

    #
    # FIXME:
    # - check refs with sources
    #
    linked_etyma = set()
    for sid in sets.intersection(linked_sets):
        for eid, sids in etyma.items():
            if sid in sids:
                linked_etyma.add(eid)
                break

    # some stats:
    forms, roots, proto = 0, 0, 0
    for l in langs.values():
        for f in l.forms:
            if f.is_root:
                roots += 1
            elif f.is_proto:
                proto += 1
            else:
                forms += 1

    print('{} forms in {} languages ({} roots, {} protoforms)'.format(forms + roots + proto, len(langs), roots, proto))
    print('assigned to {} cognate sets grouped in {} etyma'.format(
        len(sets.intersection(linked_sets)),
        len(linked_etyma),
    ))
    print('{} sources referenced {} times'.format(len(refs), sum(refs.values())))
    return sources, langs, cognates, loans, noisesets, nearsets, rootsets
