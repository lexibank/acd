import re
import itertools

import attr
from bs4 import Tag, NavigableString, BeautifulSoup as bs
from nameparser import HumanName

from .refs import clean_ref
from .util import *

__all__ = [
    'Ref', 'Gloss', 'Word', 'Source', 'Note', 'Set', 'Etymon', 'LForm', 'Language', 'Form', 'Root',
    'Loan', 'Noise', 'Near',
]


@attr.s
class Item:
    """
    An instance of a data type of the ACD, initialized from an HTML chunk.
    """
    html = attr.ib()

    @classmethod
    def match(cls, e):
        return True

    @classmethod
    def from_html(cls, e):
        if cls.match(e):
            return cls(e)

    def __json__(self):
        return {
            f.name: getattr(self, f.name) for f in attr.fields(self.__class__) if f.name != 'html'}

    def iter_refs(self):
        refs = getattr(self, 'refs', [])
        if not refs:
            if getattr(self, 'note', None):
                refs = self.note.refs
        if not refs:
            if getattr(self, 'gloss', None) and isinstance(self.gloss, Gloss):
                refs = self.gloss.refs
        for ref in refs:
            for r, pages in clean_ref(ref.label):
                yield r, pages

    def get_anchor(self):
        for a in self.html.find_all('a'):
            if 'name' in a.attrs and  re.fullmatch('[0-9]+', a['name']):
                return int(a['name'])
        raise ValueError(str(self.html))


@attr.s
class SetLike:
    id = attr.ib(default=None)  # pidno
    gloss = attr.ib(default=None)
    forms = attr.ib(default=attr.Factory(list))
    note = attr.ib(default=None)

    @staticmethod
    def get_forms(html, tablecls, formunicls, lgcls):
        """
        Forms are listed in tables, grouped into language groups.
        """
        if isinstance(formunicls, str):
            formunicls = [formunicls]
        if isinstance(lgcls, str):
            lgcls = [lgcls]
        res, group, lname = [], None, None
        forms = html.find('table', class_=tablecls) if isinstance(tablecls, str) else tablecls
        assert forms
        for tr in forms.find_all('tr'):
            g = tr.find('td', class_='group')
            if g:  # A group row.
                group = g.get_text().strip()
                continue

            bracketed = False
            for e in tr.find_all('span', class_='brax'):
                e.extract()
                bracketed = True

            # The language name is only specified in the first row of forms for the language.
            # Thus we have to remember it for later forms.
            for lcls in lgcls:
                if tr.find('td', class_=lcls):
                    language = normalize_language(
                        normalize_string(tr.find('td', class_=lcls).get_text()) or lname)
                    break
            else:
                language = lname

            for fcls in formunicls:
                f = tr.find('td', class_=fcls)
                if f:
                    form = Form(
                        html=tr,
                        language=language,
                        group=group,
                        is_loan=True,
                        fucls=f,
                        bracketed=bracketed,
                    )
                    if fcls == 'rootproto':
                        form.is_root = True

                        # FIXME: parse root set link!
                        # if 0:
                        #    slink = pform.find('a', class_='rootproto')
                        #    if slink:
                        #        self.set = slink['href']

                    lname = form.language
                    res.append(form)
                    break
        return res


@attr.s
class Near(Item, SetLike):
    """
<table class="settableNear" align="center"><tbody><tr><td class="settable">
<a name="nervous"></a>
<a name="30724"></a>
<p class="setline"><span class="keyloan"> nervous: &nbsp; anxious, nervous, restless</span></p>
<p></p><table class="entrytable"><tbody><tr><td class="entrytable">
<table class="loanforms" width="90%" align="center">
<tbody><tr valign="top">
<td class="group">WMP</td></tr>
<tr valign="top"><td class="lgloan">Cebuano</td>
<td class="formuniloan">balísa</td><td class="gloss">anxious, apprehensive</td></tr>
<tr valign="top">
<td class="lgloan">Malay</td>
<td class="formuniloan">bəlisah</td><td class="gloss">restless, fidgety</td></tr>
</tbody></table>
</td></tr></tbody></table>
<p class="setnote"><span class="lg">Malay</span> <span class="wd">bəlisah</span> points to a proto-form with *<span class="pwd">-q</span>, which <span class="lg">Cebuano</span> <span class="wd">balísa</span> supports a similar form with final vowel.  <span class="lg">Malay</span> <span class="wd">gəlisah</span> presumably is a secondary development from earlier <span class="wd">bəlisah</span>.
</p></td></tr></tbody></table>
    """
    loanform = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.id = self.get_anchor()
        self.note = Note.from_html(self.html.find('p', class_='setnote'))
        self.gloss = normalize_string(self.html.find('span', class_='keyloan').get_text())
        lf = self.html.find('span', class_='lineloanform')
        if lf:
            self.loanform = normalize_string(lf.get_text())
        self.forms = SetLike.get_forms(self.html, 'loanforms', 'formuniloan', 'lgloan')


@attr.s
class Noise(Item, SetLike):
    """
    <table class="settableNoise" align="center"><tbody><tr><td class="settable">
<a name="abundant"></a>
<a name="1658"></a>
<span class="lineloanform">(Dempwolff: *bun) </span>
<p class="setline"><span class="keyNoise">abundant</span></p>
<p></p><table class="entrytable"><tbody><tr><td class="entrytable">
<table class="noiseforms" width="90%" align="center">
<tbody><tr valign="top">
<td class="group">WMP</td></tr>
<tr valign="top"><td class="lgnoise">Malay</td>
<td class="formuninoise">bun</td><td class="gloss">croupier at a Chinese gaming mat</td></tr>
<tr valign="top">
<td class="lgnoise">Toba Batak</td>
<td class="formuninoise">bun</td><td class="gloss">abundant, of a bumper crop of rice</td></tr>
</tbody></table>
</td></tr></tbody></table>
</td></tr></tbody></table>
    """
    def __attrs_post_init__(self):
        self.id = self.get_anchor()
        self.note = Note.from_html(self.html.find('p', class_='setnote'))
        self.gloss = normalize_string(self.html.find('span', class_='keyNoise').get_text())
        lf = self.html.find('span', class_='lineloanform')
        if lf:
            self.loanform = normalize_string(lf.get_text())
        self.forms = SetLike.get_forms(self.html, 'noiseforms', 'formuninoise', 'lgnoise')


@attr.s
class Loan(Item, SetLike):
    """
    <table class="settableLoan" align="center"><tbody><tr><td class="settable">
<a name="appropriate"></a>
<a name="30345"></a>
<a name="app"></a>
<span class="lineloanform">(Dempwolff: *patut ‘proper, fitting’) </span>
<p class="setline"><span class="keyloan">appropriate: &nbsp; proper, fitting, appropriate</span></p>
<p></p><table class="entrytable"><tbody><tr><td class="entrytable">
<table class="loanforms" width="90%" align="center">
<tbody><tr valign="top">
<td class="group">WMP</td></tr>
<tr valign="top"><td class="lgloan">Maranao</td>
<td class="formuniloan">patot</td><td class="gloss">proper, fitting, due</td></tr>
<tr valign="top">
<td class="lgloan">Javanese</td>
<td class="formuniloan">patut</td><td class="gloss">suitable, well-advised, appropriate</td></tr>
</tbody></table>
</td></tr></tbody></table>
<p class="setnote">Borrowing from <span class="lg">Javanese</span> into <span class="lg">Malay</span>, with subsequent wide dispersal via <span class="lg">Malay</span>. <span class="bib"><a class="bib" href="acd-bib.htm#Dempwolff">Dempwolff (1938)</a></span> compared the <span class="lg">Ngaju Dayak</span>, <span class="lg">Malay</span>, <span class="lg">Javanese</span> and <span class="lg">Toba Batak</span> forms with <span class="lg">Tagalog</span> <span class="wd">patot</span> ‘proper, fitting’ and posited Uraustronesisch *<span class="pwd">patut</span> ‘proper, fitting’, but I have been unable to find the last of these forms in any modern dictionary.  Note the close semantics and probable origin in <span class="lg">Javanese</span> with subsequent spread by <span class="lg">Malay</span> for both this form and <span class="lg">Malay</span> <span class="wd">pantas</span>, etc.
</p></td></tr></tbody></table>
    """
    loanform = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.id = self.get_anchor()
        self.note = Note.from_html(self.html.find('p', class_='setnote'))
        self.gloss = normalize_string(self.html.find('span', class_='keyloan').get_text())
        lf = self.html.find('span', class_='lineloanform')
        if lf:
            self.loanform = normalize_string(lf.get_text())
        self.forms = SetLike.get_forms(self.html, 'loanforms', 'formuniloan', 'lgloan')


@attr.s
class FormLike:
    form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    is_proto = attr.ib(default=False)
    is_loan = attr.ib(default=False)


@attr.s
class Ref(Item):
    # The key s a fragment ID in the bib, but it's largely useless, because it's just the (last
    # word of) the last name of the first author mentioned in the label. Basically just
    # self.label.split(',')[0].
    key = attr.ib(default=None)
    label = attr.ib(default=None)
    year = attr.ib(default=None)

    def __json__(self):
        return self.label

    @classmethod
    def match(cls, e):
        return isinstance(e, Tag) and e.name == 'span' and \
               ('class' in e.attrs) and e['class'][0] == 'bib'

    def __attrs_post_init__(self):
        link = self.html.find('a')
        self.key = link['href'].split('#')[1]
        self.label = link.text
        m = re.search('(?P<year>[0-9]{4}[a-z]?)', self.label)
        if m:
            self.year = m.group('year')


@attr.s
class Gloss(Item):
    """
    Glosses may contain markup such as refs.

    <span class="FormGloss">type of ocean fish (<span class="bib"><a class="bib" href="acd-bib.htm#Headland">Headland and Headland (1974)</a></span>), kind of marine eel (<span class="bib"><a class="bib" href="acd-bib.htm#Reid">Reid (1971:186)</a></span>)</span>
    """
    refs = attr.ib(default=attr.Factory(list))
    markdown = attr.ib(default='')
    plain = attr.ib(default='')

    @classmethod
    def match(cls, e):
        return isinstance(e, Tag) and e.name == 'span' and \
               ('class' in e.attrs) and e['class'][0] == 'FormGloss'

    def __attrs_post_init__(self):
        # Strip refs and markup
        for c in self.html.contents:
            if isinstance(c, NavigableString):
                self.plain += str(c)
                self.markdown += str(c)
            else:
                assert c.name in ['span', 'i', 'xlg', 'wd', 'ha', 'in'], str(c)
                ref = Ref.from_html(c)
                if ref:
                    self.refs.append(ref)
                    self.markdown += '[{}](bib-{})'.format(ref.label, ref.key)
                elif (('class' in c.attrs) and c['class'] in ('wd', 'lg')) \
                        or c.name in ('i', 'xlg', 'wd', 'ha', 'in'):
                    self.plain += c.text
                    self.markdown += '_{}_'.format(c.text)
        self.plain = normalize_string(self.plain)
        self.plain = re.sub(r'\s+\(\)', '', self.plain.strip())


@attr.s
class Word(Item, FormLike):
    """
    A form as parsed from the words pages.

    <span class="FormHw">a</span>
    <span class="FormLg">Aklanon</span>
    <span class="FormGroup">(WMP)</span>
    <span class="FormGloss">exclamation of discovery; "ah" (with high intonation)</span> <span class="pLang">PMP </span> <a class="setword2" href="acd-s_a1.htm#380">*<span class="pForm">a₃</span></a>
    <span class="FormPw">*abih</span><span class="FormPLg">PCha</span><span class="FormGroup">(WMP)</span> <span class="FormGloss">all</span> <span class="pLang">PWMP </span> <a class="setword2" href="acd-s_q.htm#4102">*<span class="pForm">qabiq</span>
    """
    language = attr.ib(default=None)
    group = attr.ib(default=None)
    proto_language = attr.ib(default=None)
    proto_form = attr.ib(default=None)
    cognateset = attr.ib(default=None)

    def __attrs_post_init__(self):
        for class_, attrib in [
            ('FormHw', 'form'),
            ('FormLg', 'language'),
            ('FormPw', 'form'),
            ('FormPLg', 'language'),
            ('FormGroup', 'group'),
            ('FormGloss', 'gloss'),
            ('pLang', 'proto_language'),
            ('pForm', 'proto_form'),
        ]:
            e = self.html.find('span', class_=class_)
            if e:
                if class_ == 'FormPw':
                    self.is_proto = True
                if class_ == 'FormGloss':
                    setattr(self, attrib, Gloss(html=e))
                else:
                    setattr(self, attrib, normalize_string(e.get_text().strip()))
        if self.language in ['PRuk', 'PAty']:
            # In two cases, proto words are not marked up correctly:
            self.is_proto = True
        self.form = parse_form(self.form, self.is_proto)
        e = self.html.find('a', class_="setword2", href=True)
        if e:
            m = re.search('acd-(?P<module>s|f)_(?P<letter>[a-z0-9]+)\.htm#(?P<number>[0-9]+)', e['href'])
            if m:
                self.cognateset = (m.group('module'), m.group('letter'), m.group('number'))
            else:
                raise ValueError(e['href'])


@attr.s
class Source(Item):
    author = attr.ib(default=None)
    year_ = attr.ib(default=None)
    title = attr.ib(default=None)
    text = attr.ib(default=None)
    bibline2 = attr.ib(default=False)

    def __json__(self):
        return {
            'authors': self.authors,
            'year': self.year,
            'key': self.key,
            'title': self.title,
            'text': self.text,
        }

    def __attrs_post_init__(self):
        years = {
            'Blust': {
                'A Murik vocabulary, with a note on the linguistic position of Murik': '1974b',
                'Subgrouping, circularity and extinction: some issues in Austronesian comparative linguistics': '1999a',
                'The history of faunal terms in Austronesian languages': '2002a',
                'Fieldnotes on Atoni, July, 1973': '1973a',
                'The Austronesian Comparative Dictionary: A Work in Progress.': '2013a',
            },
            'Fox': {
                'Our ancestors spoke in pairs: Rotinese views of language, dialect, and code': '1874a',
            },
            'Lichtenberk': {
                'Food preparation': '1998a',
            },
            'Osmond': {
                'The Landscape': '2003a',
                'The seascape': '2003b',
                'Mammals, reptiles, amphibians': '2011b',
            }
        }
        for cls, attrib in [
            ('Author', 'author'),
            ('PubYear', 'year_'),
            ('RefTitle', 'title'),
            ('RefText', 'text'),
        ]:
            e = self.html.find('span', class_=cls)
            if e:
                text = e.get_text()
                if attrib == 'author' and self.bibline2 and text:
                    # concatenate!
                    assert self.author
                    self.author = '{}, {}'.format(self.author, text)
                else:
                    setattr(self, attrib, e.get_text())
        #ak = self.author.split(',')[0]
        #if self.title in years.get(ak, []):
        #    self.year_ = years[ak][self.title]

    @property
    def authors(self):
        def name(s):
            if s.endswith('.') and ',' not in s:
                s = s[:-1].strip()
            return HumanName(s)

        commas = self.author.count(',')
        if commas < 2:
            return [name(chunk.strip()) for chunk in self.author.split(' and ')]
        chunks = [c.strip() for c in self.author.split(',')]
        res = [name('{}, {}'.format(chunks.pop(0), chunks.pop(0)))]
        for chunk in chunks:
            if chunk:
                for n in chunk.split(' and '):
                    n = n.strip()
                    if n:
                        res.append(name(n))
        return res

    @property
    def year(self):
        m = re.search('(?P<year>[0-9]{4}(/[0-9]{2})?[a-z]?)', normalize_years(self.year_ or ''))
        if m:
            return m.group('year')
        return self.year_

    @property
    def key(self):
        authors = self.authors
        if len(authors) == 2:
            key = '{} and {}'.format(authors[0].last or authors[0].first, authors[1].last or authors[1].first)
        elif len(authors) == 3:
            key = '{}, {} and {}'.format(
                authors[0].last or authors[0].first,
                authors[1].last or authors[1].first,
                authors[2].last or authors[2].first,
                )
        else:
            key = authors[0].last or authors[0].first
            if len(authors) > 1:
                key += ' et al.'

        return '{} {}'.format(key, self.year or 'nd')


@attr.s
class Note(Item):
    """
    <p class="setnote">
    <span class="note">Note: &nbsp; </span>
    <span class="bib"><a class="bib" href="acd-bib.htm#Egerod">Egerod (1965)</a></span>
    describes three "passives'' for
    <span class="lg">Atayal</span>: (1) a "relational passive'', (2) an "indefinite passive'', and (3) a "definite passive''.  The definite passive can occur in any of five aspects, of which the "neutral definite passive'' is marked by <span class="wd">-an</span>, while the "negatable neutral definite passive'' and the "imperative definite passive'' are marked by <span class="wd">-i</span>.  The paradigmatic alternation of <span class="wd">-an</span> and <span class="wd">-i</span> thus appears to be common to at least <span class="lg">Atayal</span> and <span class="lg">Bikol</span>.  The present affix evidently is identical to what <span class="bib"><a class="bib" href="acd-bib.htm#Wolff">Wolff (1973:73)</a></span> called the "local passive dependent'' construction. It seems to have marked imperatives of a certain type, but may have been used with a wider range of construction types than I have indicated here.
    <a class="root" href="acd-r_b.htm#-baw₁"><span class="pwd">-baw₁</span></a>
    """
    refs = attr.ib(default=attr.Factory(list))
    plain = attr.ib(default='')
    markdown = attr.ib(default='')

    @classmethod
    def match(cls, e):
        return isinstance(e, Tag) and e.name == 'p' and (e['class'][0] in ('setnote', 'pnote'))

    def __attrs_post_init__(self):
        for c in self.html.contents:
            if isinstance(c, NavigableString):
                self.plain += str(c)
                self.markdown += str(c)
            else:
                cls = c['class'][0] if 'class' in c.attrs else None
                assert c.name in ['span', 'i', 'a', 'xlg', 'b', 'pn', 'br', 'xplg', 'font', 'um'], str(c)
                if c.name == 'span':
                    if cls == 'phoneme':
                        c, cls = c.find('span'), 'wd'
                    elif cls == 'note':
                        continue
                    assert cls in (None, 'wd', 'pwd', 'lg', 'plg', 'bib', 'proto', 'note', 'fam'), str(c)
                ref = Ref.from_html(c)
                if ref:
                    self.refs.append(ref)
                    self.markdown += '[{}](bib-{})'.format(ref.label, ref.key)
                elif c.name == 'br':
                    self.plain += '\n'
                    self.markdown += '\n\n'
                elif c.name == 'font':
                    self.plain += c.get_text()
                    self.markdown += str(c)
                elif c.name == 'b':
                    self.plain += c.get_text()
                    self.markdown += '__{}__'.format(c.get_text())
                elif (cls in ('lg', 'plg', 'fam')) or c.name in ('xlg', 'xplg'):
                    self.plain += c.get_text()
                    self.markdown += '__language__{}__'.format(c.get_text())
                elif c.name == 'a':
                    self.plain += c.get_text()
                    if cls == 'root':
                        self.markdown += '[{}](root-{})'.format(c.get_text(), c['href'])
                    else:
                        if cls:
                            raise ValueError(c)
                        self.markdown += c.get_text()
                elif c.name == 'span' and cls is None:
                    self.plain += c.get_text()
                    self.markdown += c.get_text()
                elif (cls in ('wd', 'pwd', 'proto')) or c.name in ('i', 'wd', 'ha', 'in', 'pn', 'um'):
                    self.plain += c.text
                    self.markdown += '_{}_'.format(c.text)
                else:
                    raise ValueError(str(c))
        self.plain = re.sub('\s+\(\)', '', self.plain).strip()
        self.markdown = self.markdown.strip().replace('*', '&ast;')
        for a in ['plain', 'markdown']:
            setattr(self, a, re.sub(r'^Note:\s+', '', getattr(self, a)))


@attr.s
class Set(Item, SetLike):
    """
    1) Entries begin with an abbreviation for the proto-language to which the etymon is assigned.  This is followed on the same line by the reconstructed form marked by an asterisk indicating that it has been inferred by application of the Comparative Method, and then a gloss.

    2) The next line contains supporting evidence, beginning with a subgroup label followed by language names that are generally cited in a north-to-south and west-to-east order, then the reflex of the reconstructed form and a gloss that is an exact or nearly exact copy of the meaning given in the primary source.

    An example of a maximally simple comparison which contains only these features is the following:

    Entry (1)

    PMP *baliq ‘fracture, break’

        WMP: Tagalog báliʔ ‘fracture, break along the length; fractured, broken’
	        Aklanon báliʔ ‘get broken in two, get fractured (as an arm)’

        CMP:  Hawu ɓari ‘broken, in pieces’

    see Trussel and Blust paper

    <td class="entrytable">
        <p class="pidno">9625</p>
        <a name="saku₃"></a>
        <p class="pLang">
            <span class="pcode">POC</span> &nbsp; &nbsp;
            <span class="lineform">*saku₃ </span>
            <span class="linegloss"><a class="setline" href="acd-ak_k.htm#kind">kind </a> of  <a class="setline" href="acd-ak_b.htm#banana">banana</a> </span>
            <span class="dbl">[doublet: <a href="acd-s_t.htm#5496">*tabuRiq</a>]<span>
            <span class="dsj">[disjunct: <a href="acd-s_z.htm#9437">*zizir</a>]<span>
        </p>

        <table class="forms" width="90%" align="center">
            <tbody>
                <tr valign="top">
                    <td class="group">OC</td>
                </tr>
                <tr valign="top">
                </tr>
                <tr valign="top">
                    <td class="lg"><a href="acd-l_P.htm#Paamese"><span class="lg">Paamese</span></a></td>
                    <td class="formuni">sou-sou <span class="Met"><sup>&lt;M</sup></span></td>
                    <td class="gloss">kind of banana</td>
                </tr>
                <tr valign="top">
                    <td class="lg">&nbsp;</td>
                    <td class="formuni">sau-sau</td><td class="gloss">kind of banana (southern dialect)</td></tr>
            </tbody>
        </table>
    </td>
    <p class="pidno">8060</p>
    <a name="tanoq"></a>
    <p class="pLang">
        <span class="pcode">POC</span> &nbsp; &nbsp;
        <span class="lineform">*tanoq </span>
        <span class="linegloss"><a class="setline" href="acd-ak_e.htm#earth">earth, </a> <a class="setline" href="acd-ak_s.htm#soil">soil, </a> <a class="setline" href="acd-ak_l.htm#land">land; </a> <a class="setline" href="acd-ak_d.htm#down">down; </a> <a class="setline" href="acd-ak_w.htm#westward">westward</a> </span>
    </p>
    <table class="forms" width="90%" align="center">
    """
    subset = attr.ib(default=0)
    key = attr.ib(default=None)
    lookup = attr.ib(default=attr.Factory(list))
    proto_language = attr.ib(default=None)
    doublet_text = attr.ib(default=None)
    disjunct_text = attr.ib(default=None)
    doublets = attr.ib(default=attr.Factory(list))
    disjuncts = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        # self.html = p class="pidno"
        from acdparser import RECONCSTRUCTIONS
        name = next_tag(self.html)
        assert name.name == 'a'
        lang = next_tag(name)
        assert lang.name == 'p'
        forms = lang.find('table', class_='forms') or next_tag(lang)
        if forms and forms.name == 'p':
            forms = None
        assert name.name == 'a' and lang.name == 'p' and ((forms is None) or forms.name == 'table'), str(self.html.parent)

        self.id = int(self.html.text)
        assert self.id
        self.key = normalize_string(lang.find('span', class_='lineform').text)
        self.gloss = normalize_string(lang.find('span', class_='linegloss').get_text())
        pcode = lang.find('span', class_='pcode')
        if pcode:
            self.proto_language = pcode.get_text()
        assert self.proto_language in RECONCSTRUCTIONS, '{}'.format(self.proto_language)

        for cls, attrib in [('dsj', 'disjunct'), ('dbl', 'doublet')]:
            e = lang.find('span', class_=cls)
            if e:
                setattr(self, attrib + '_text', re.sub(r'\[{}:\s*'.format(attrib), '', e.get_text().replace(']', '')))
                for a in e.find_all('a', href=True):
                    getattr(self, attrib + 's').append((a.text, set_from_href(a)))

        if forms:
            pnote = forms.find('p', class_='pnote')
            if pnote:
                if pnote.find('p', class_='pnote'):
                    pnote = pnote.find('p', class_='pnote')
                self.note = Note.from_html(pnote)
            self.forms = SetLike.get_forms(forms, forms, 'formuni', 'lg')


@attr.s
class Etymon(Item):
    """
    <a name=ma-₁></a>
    <p class="setline">
        <span class="key">*ma-₁</span>
        <span class = "setline">
            <a class = "setline" href="acd-ak_s.htm#stative">stative </a>
            <a class = "setline" href="acd-ak_p.htm#prefix">prefix</a>
        </span>
    </p>
    """
    id = attr.ib(default=None)
    key = attr.ib(default=None)
    gloss = attr.ib(default=None)
    sets = attr.ib(default=attr.Factory(list))
    note = attr.ib(default=None)
    formosan_only = attr.ib(default=False)

    def __attrs_post_init__(self):
        self.formosan_only = self.html['class'][0] == 'SettableF'
        prev = self.html.previous_sibling
        while not isinstance(prev, Tag):
            prev = prev.previous_sibling
        if prev.name == 'p' and prev['class'][0] == 'setnum':
            self.id = int(prev.text)
        assert self.id
        self.key = self.html.find('span', class_='key').text.strip()
        self.gloss = self.html.find('span', class_='setline').get_text().strip()
        self.note = Note.from_html(self.html.find('p', class_='setnote'))

        subset_index = 0
        for e in self.html.find_all('p', class_='pidno'):
            # FIXME:
            p = previous_tag(e)
            assert (p and p.name in ('a', 'p')) or e.parent.name == 'td', str(e.parent)
            if not (p and p.name in ('a', 'p')):
                # we're starting a new table of reconstructions
                subset_index += 1
            self.sets.append(Set(html=e, subset=subset_index))
        #if self.formosan_only:
        #    print('F', self.id)


@attr.s(auto_detect=True)
class LForm(Item, FormLike):
    """
    <p class="formline"><a href="acd-s_t.htm#7351">tood</a><span class="formdef">knee</span>
    (PMP: *<a class="pform" href="acd-s_t.htm#7351">tuhud</a>)
    *<a class="setkey" href="acd-s_t.htm#30356">tuduS</a>
    <span class="showdial"><a class="dialname" href="#Yami_(Iraralay)">Iraralay</a></span>
    </p>

    <p class="formline"><a href="acd-n_f.htm#2376">labaih</a>
    <span class="formdef">careless, without worries <span class="bib"><a class="bib" href="acd-bib.htm#(Ferrell">(Ferrell 1969)</a></span></span>
    (<a class="pformN" href="acd-n_f.htm#2376">NOISE</a>)
    </p>

    acd-l_n.htm:<p class="formline"><a href="acd-s_b.htm#560">bhalé (*i &gt; é unexpl.)</a><span class="formdef">change, exchange, alter</span>

    acd-w_b.htm:<p class="formline"><span class="FormHw">bhalé (*i &gt; é unexpl.)</span><span class="FormLg">Ngadha</span><span class="FormGroup">(CMP)</span> <span class="FormGloss">change, exchange, alter</span> <span class="pLang">PMP</span> <a class="setword2" href="acd-s_b.htm#560">*<span class="pForm">baliw₂</span></a>
    """
    href = attr.ib(default=None)
    sets = attr.ib(default=attr.Factory(set))
    note = attr.ib(default=None)
    is_root = attr.ib(default=False)
    ass = attr.ib(default=False)
    met = attr.ib(default=False)

    def __attrs_post_init__(self):
        link = self.html.find('a', href=True)
        self.href = link['href']
        self.form = parse_form(link.text.strip(), True)
        self.gloss = Gloss(self.html.find('span', class_='formdef'))

        for a in self.html.find_all('a', class_=True, href=True):
            if a['class'][0] == 'setkey' or a['class'][0].startswith('pform'):
                self.sets.add(set_from_href(a))
        if 'r' in {s[0] for s in self.sets}:
            self.is_root = True
        # Fix sets:
        ns = set()
        for cat, no in self.sets:
            if int(no) in [30144, 30269, 30262, 30324, 30351]:
                cat = 'near'
            ns.add((cat, no))
        self.sets = ns


@attr.s
class Language(Item):
    """
    <p class="langline">
      <a name="19190"></a>2. <span class="langname">Abaknon</span>
      <span class="langcount">(27)</span>
      <span class="langgroup"><a class="grouplink" href="acd-g_w.htm#Abaknon">WMP</a></span>
      <span class="bibref">(<span class="bib"><a class="bib" href="acd-bib.htm#Jacobson">Jacobson 1999</a></span>)</span>
      <span class="ISOline">
        [<a class="ISO" href="http://www.ethnologue.com/show_language.asp?code=abx"><span class="ISO">abx</span></a>]
        (<span class="ISOname">Inabaknon</span>)
        <span class="Loc">Philippines</span>
      </span>
      <span class="aka">[aka: Inabaknon]</span>
    </p>

    <p class="dialpara">
        <a name="819"></a>
        <span class="langname"><a href="#Manobo">Manobo</a> (Western Bukidnon)</span>
        <span class="langcount">(1013)</span>
        <span class="langgroup"><a class="grouplink" href="acd-g_w.htm#Manobo_(Western_Bukidnon)">WMP</a></span>
        <span class="bibref">(<span class="bib"><a class="bib" href="acd-bib.htm#Elkins">Elkins 1968</a></span>)</span>
        <span class="ISOline">
            [<a class="ISO" href="http://www.ethnologue.com/show_language.asp?code=mbb"><span class="ISO">mbb</span></a>]
            (<span class="ISOname">Manobo, Western Bukidnon</span>)
            <span class="Loc">Philippines</span>
        </span>
    </p>

    <p class="formline"><a href="acd-s_t.htm#7351">tood</a><span class="formdef">knee</span>
    (PMP: *<a class="pform" href="acd-s_t.htm#7351">tuhud</a>)
    *<a class="setkey" href="acd-s_t.htm#30356">tuduS</a>
    <span class="showdial"><a class="dialname" href="#Yami_(Iraralay)">Iraralay</a></span>
    </p>
    <p class="formline"><a href="acd-s_w.htm#5954">wa-wawo</a><span class="formdef">eight (of humans)</span>
    (PAN: *<a class="pform" href="acd-s_w.htm#5954">wa-walu</a>)
    *<a class="setkey" href="acd-s_w.htm#28735">walu</a>
     <span class="showdial"><a class="dialname" href="#Yami_(Iraralay)">Iraralay</a>

    <p class="lbreak">
    """
    id = attr.ib(default=None)
    name = attr.ib(default=None)
    group = attr.ib(default=None)
    isocode = attr.ib(default=None)
    isoname = attr.ib(default=None)
    location = attr.ib(default=None)
    aka = attr.ib(default=None)
    nwords = attr.ib(default=None)
    refs = attr.ib(default=attr.Factory(list))
    parent_language = attr.ib(default=None)
    is_dialect = attr.ib(default=False)
    forms = attr.ib(default=attr.Factory(list))
    abbr = attr.ib(default=None)
    is_proto = attr.ib(default=False)

    def __attrs_post_init__(self):
        prev = previous_tag(self.html)
        if prev and prev.name == 'p':
            prev = prev.contents[-1]
            if not isinstance(prev, Tag):
                prev = previous_tag(prev)
        if prev and prev.name == 'a' and prev.has_attr('name'):
            self.abbr = prev['name']
        self.name = self.html.find('span', class_='langname').get_text()
        if self.html['class'][0] == 'dialpara':
            self.is_dialect = True
            try:
                self.parent_language = self.html.find('span', class_='langname').find('a').text
            except:
                pass
        self.id = int(self.html.find('a')['name'])
        self.group = self.html.find('span', class_='langgroup').get_text()
        self.nwords = int(self.html.find('span', class_='langcount').text.replace('(', '').replace(')', ''))

        bibref = self.html.find('span', class_='bibref')
        if bibref:
            for c in bibref.contents:
                ref = Ref.from_html(c)
                if ref:
                    self.refs.append(ref)

        for attrib, cls in [
            ('isocode', 'ISO'),
            ('isoname', 'ISOname'),
            ('location', 'Loc'),
            ('aka', 'aka'),
        ]:
            e = self.html.find('span', class_=cls)
            if e:
                setattr(self, attrib, e.get_text())

        assert (self.isocode is None) or re.fullmatch('[a-z]{3}', self.isocode), self.isocode

        form = next_tag(self.html)
        while (len(self.forms) < self.nwords) or \
                (form and form.name == 'p' and form['class'][0] == 'formline') or \
                (form and form.name == 'p' and form['class'][0] == 'lbreak'):
            if form is None or form.name != 'p':
                break
            if form['class'][0] == 'lbreak':
                form = next_tag(form)
            if form.name != 'p':
                break
            assert form['class'][0] == 'formline'
            self.forms.append(LForm(html=form, is_proto=self.is_proto))
            form = next_tag(form)

        if self.name == 'Sasak':
            self.forms.append(LForm(
                html=bs("""\
<p class="formline"><a href="acd-s_t.htm#10372">tetes</a><span class="formdef">peck open an egg (of a hatching chick)</span>
(WMP: *<a class="pform" href="acd-s_t.htm#10372">testes</a>)
*<a class="setkey" href="acd-s_t.htm#10372">testes</a>
</p>""", 'lxml'),
                is_proto=self.is_proto))

        assert self.nwords + 20 > len(self.forms) >= self.nwords
        # Merge forms:
        dedup = []
        for _, forms in itertools.groupby(
                sorted(self.forms, key=lambda f: (f.form, f.gloss.plain)), lambda f: (f.form, f.gloss.plain)
        ):
            forms = list(forms)
            form = forms[0]
            for f in forms[1:]:
                form.sets = form.sets.union(f.sets)
            dedup.append(form)

        self.forms = dedup
        if self.abbr:
            if self.abbr == self.name:
                self.abbr = None
            else:
                self.abbr = self.abbr.lower()
        self.is_proto = self.name.startswith('Proto-')


@attr.s
class Form(Item, FormLike):
    """
    # form in proto language:
    <tr valign="top"><td class="lgP">PSS</td>
    <td class="rootproto">*tamba(k)</td><td class="gloss">hit, pound</td></tr>

    # form in proto language with set link:
    <tr valign="top"><td class="lgP">PWMP</td>
    <td class="rootproto">*<a class="rootproto" href="acd-s_t.htm#5640">ti(m)bak</a></td><td class="gloss">clap, make a clapping sound</td></tr>

    # form in language
    <tr valign="top"><td class="lg">Yamdena</td>
    <td class="formuni">ambak</td><td class="gloss">pound into the ground; stamp with the feet</td></tr>

    <tr valign="top"><td class="lg"><span class="brax">[</span><a href="acd-l_A.htm#'Āre'āre"><span class="lg">'Āre'āre</span></a></td>
    <td class="formuni">mā ni ʔaʔe</td><td class="gloss">core of a boil<span class="brax">]</span></td></tr>

    acd-s_b.htm:<td class="formuni">bhalé <span class="hwnote">*i &gt; é unexpl.</span></td><td class="gloss">change, exchange, alter</td></tr>
    """
    group = attr.ib(default=None)
    language = attr.ib(default=None)
    is_root = attr.ib(default=False)
    set = attr.ib(default=None)
    bracketed = attr.ib(default=False)
    ass = attr.ib(default=False)
    met = attr.ib(default=False)
    note = attr.ib(default=None)
    fucls = attr.ib(default='formuni')

    def __attrs_post_init__(self):
        self.gloss = Gloss(html=self.html.find('td', class_='gloss'))
        formuni = self.html.find('td', class_=self.fucls) if isinstance(self.fucls, str) else self.fucls
        for cls in ['Met', 'Ass', 'hwnote']:
            o = formuni.find('span', class_=cls)
            if o:
                setattr(self, cls.lower().replace('hw', ''), o.text if cls == 'hwnote' else True)
                o.extract()

            self.form = formuni.get_text()

        if self.language.startswith('Proto-'):
            self.is_proto = True
        self.form = parse_form(self.form, self.is_proto)
        assert self.language and self.form
        self.fucls = None


@attr.s
class Root(Item, SetLike):
    """
    <td>
    <a name="-baj"></a>
    <p class="SetIdno">29829</p>
    <a name="29829"></a>
    <p class="setline"><span class="key">*-baj</span> <span class="setline">unravel, untie</span></p>
    <table class="formsR" width="90%" align="center">
    <tbody>
    ... Forms ...
    <p class="setnote"><span class="lg">Isneg</span> <span class="wd">ubād</span> 'untie, unbind, let loose' (expected **<span class="wd">ubag</span>) suggests that <span class="lg">Aklanon</span> <span class="wd">húbad</span> may not contain the root *<span class="pwd">-baj</span>.
    </p></td>
    """
    key = attr.ib(default=None)

    def __attrs_post_init__(self):
        self.note = Note.from_html(self.html.find('p', 'setnote'))
        self.id = int(self.html.find('p', class_='SetIdno').text)
        self.key = self.html.find('span', class_='key').text
        self.gloss = self.html.find('span', class_='key').get_text()

        self.forms = SetLike.get_forms(self.html, 'formsR', ('rootproto', 'formuni'), ('lg', 'lgP'))
