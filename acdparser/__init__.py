import json
import collections

from nameparser import HumanName

from acdparser.parser import *

INVALID_LANGS = ['Kaniet (Thilenius)']


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, HumanName):
            return {'first': obj.first, 'middle': obj.middle, 'last': obj.last}
        return json.JSONEncoder.default(self, obj)


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
        if lang.id in langs:
            # Proto-Western Micronesian is listed twice ...
            assert int(lang.id) == 19629
            assert lang.nwords == langs[lang.id].nwords
            langs[lang.id].abbr = 'pwmc'
            continue
        langs[lang.id] = lang
    assert len(langs) == len(set(l.name for l in langs.values())), 'duplicate language name'
    # So now, language names and ids are unique.

    forms, linked_sets = set(), set()
    for l in langs.values():
        for form in l.forms:
            refs.update([r for r, _ in form.iter_refs()])
            forms.add((l.name, form.form))
            for cat, no in form.sets:
                if cat in ['f', 's']:
                    linked_sets.add(int(no))

    # We provide language forms for simple lookup:
    forms_by_lang = {}
    for l in langs.values():
        forms_by_lang[l.name] = {(f.form, f.gloss.plain): f for f in l.forms}
    for l in langs.values():
        # Proto forms are listed with abbreviated language name.
        if l.abbr and l.abbr not in forms_by_lang:
            forms_by_lang[l.abbr] = forms_by_lang[l.name]

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
        refs.update([r for r, _ in e.iter_refs()])
        for s in e.sets:
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
                lform.form = f.form
                lform.note = f.note
                lform.is_root = f.is_root
                lform.ass = f.ass
                lform.met = f.met

    #
    # FIXME:
    # - check refs with sources
    # - include pseudo cognate sets: Noise, Near, Loan,
    # - include roots
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
    return sources, langs, cognates

    for s in RootParser():
        if s.note and s.note.plain:
            print(s.note.markdown)
