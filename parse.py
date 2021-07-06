import re
import pathlib
import itertools
import collections

from nameparser import HumanName
import attr
import lxml
import cchardet
from bs4 import BeautifulSoup as bs, NavigableString, Tag


def normalize_years(ref):
    ref = re.sub(r'\-([0-9]{4})', lambda m: '/' + m.groups()[0][2:], ref)
    return re.sub(r'\-([0-9]{2})', lambda m: '/' + m.groups()[0], ref)


def form_and_note(s):
    return re.sub(r'\s+', ' ', s), None
    note = None
    if '(' in s and s.endswith(')'):
        s, _, note = s[:-1].partition('(')
    return s.strip(), note.strip() if note else None


def previous_tag(e):
    n = e.previous_sibling
    if n is None:
        return
    while not isinstance(n, Tag):
        n = n.previous_sibling
        if n is None:
            return
    return n


def next_tag(e):
    n = e.next_sibling
    if n is None:
        return
    while not isinstance(n, Tag):
        n = n.next_sibling
        if n is None:
            return
    return n


class Parser:
    __tag__ = (None, None)
    __cls__ = None
    __glob__ = 'acd-*.htm'

    def __init__(self, d=pathlib.Path('raw')):
        patterns = [self.__glob__] if isinstance(self.__glob__, str) else self.__glob__
        self.paths = list(itertools.chain(
            *[sorted(list(d.glob(g)), key=lambda p: p.name) for g in patterns]))

    def include(self, p):
        return True

    @staticmethod
    def fix_html(s):
        for src, t in [
            ('</wd?', '</span>'),
            ('</wad>', '</span>'),
            ('>/wd>', '</span>'),
            ('>wd>', '<span class="wd">'),
            (r'</\wd>', '</span>'),
            (r'<pkg>', '<span>'),
            ('t<m>alam', '<span class="wd">talam</span>'),
            ('</span><a> ', '</span></a> '),
            ('<p class="pnote"><hr><p class="pnote">', '<p class="pnote"'),
            (' </span>ka-asgad-án</span> ', ' <span class="wd">ka-asgad-án</span> '),
        ]:
            s = s.replace(src, t)
        s = re.sub(
            r'<a name=(?P<abbr>[A-Za-z]+)></span>',
            lambda m: '<a name="{}"></a>'.format(m.group('abbr')),
            s)
        return s

    def iter_html(self):
        for p in self.paths:
            if self.include(p):
                #print(p)
                yield bs(self.fix_html(p.read_text(encoding='utf8')), 'lxml')

    def __iter__(self):
        for html in self.iter_html():
            classes = self.__tag__[1]
            if isinstance(classes, str):
                items = html.find_all(self.__tag__[0], class_=classes)
            else:
                items = [
                    i for i in html.find_all(self.__tag__[0], class_=True)
                    if i['class'][0] in classes]
            for e in items:
                o = self.__cls__.from_html(e)
                if o:
                    yield o
                else:
                    print('skipping: {}'.format(str(e)[:50]))


@attr.s
class Item:
    html = attr.ib()

    @classmethod
    def match(cls, e):
        return True

    @classmethod
    def from_html(cls, e):
        if cls.match(e):
            return cls(e)


@attr.s
class Ref(Item):
    key_ = attr.ib(default=None)
    label = attr.ib(default=None)
    year = attr.ib(default=None)

    @classmethod
    def match(cls, e):
        return isinstance(e, Tag) and e.name == 'span' and \
            ('class' in e.attrs) and e['class'][0] == 'bib'

    @property
    def key(self):
        return '{}-{}'.format(self.key_, self.year or 'nd')

    def __attrs_post_init__(self):
        link = self.html.find('a')
        self.key_ = link['href'].split('#')[1]
        self.label = link.text
        m = re.search('(?P<year>[0-9]{4}[a-z]?)', self.label)
        if m:
            self.year = m.group('year')


@attr.s
class Gloss(Item):
    """
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
        self.plain = re.sub(r'\s+\(\)', '', self.plain.strip())
        self.plain = re.sub(r'\s+', ' ', self.plain)


@attr.s
class Word(Item):
    """
    <span class="FormHw">a</span>
    <span class="FormLg">Aklanon</span>
    <span class="FormGroup">(WMP)</span>
    <span class="FormGloss">exclamation of discovery; "ah" (with high intonation)</span> <span class="pLang">PMP </span> <a class="setword2" href="acd-s_a1.htm#380">*<span class="pForm">a₃</span></a>
    <span class="FormPw">*abih</span><span class="FormPLg">PCha</span><span class="FormGroup">(WMP)</span> <span class="FormGloss">all</span> <span class="pLang">PWMP </span> <a class="setword2" href="acd-s_q.htm#4102">*<span class="pForm">qabiq</span>
    """
    headword = attr.ib(default=None)
    language = attr.ib(default=None)
    group = attr.ib(default=None)
    proto_language = attr.ib(default=None)
    proto_form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    cognateset = attr.ib(default=None)
    is_proto = attr.ib(default=False)
    note = attr.ib(default=None)

    def __attrs_post_init__(self):
        for class_, attrib in [
            ('FormHw', 'headword'),
            ('FormLg', 'language'),
            ('FormPw', 'headword'),
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
                    try:
                        setattr(self, attrib, Gloss(html=e))
                    except:
                        print(e)
                        raise
                else:
                    setattr(self, attrib, re.sub(r'\s+', ' ', e.get_text().strip()))
        self.headword, self.note = form_and_note(self.headword)
        if self.language in ['PRuk', 'PAty']:
            # In two cases, proto words are not marked up correctly:
            self.is_proto = True
        if self.is_proto and self.headword.startswith('*'):
            self.headword = self.headword[1:].strip()
        e = self.html.find('a', class_="setword2", href=True)
        if e:
            m = re.search('acd-(?P<module>s|f)_(?P<letter>[a-z0-9]+)\.htm#(?P<number>[0-9]+)', e['href'])
            if m:
                self.cognateset = (m.group('module'), m.group('letter'), m.group('number'))
            else:
                raise ValueError(e['href'])


class WordParser(Parser):
    __glob__ = 'acd-w_*.htm'
    __cls__ = Word
    __tag__ = ('p', 'formline')


@attr.s
class Source(Item):
    author = attr.ib(default=None)
    year_ = attr.ib(default=None)
    title = attr.ib(default=None)
    text = attr.ib(default=None)
    bibline2 = attr.ib(default=False)

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


class SourceParser(Parser):
    __glob__ = 'acd-bib.htm'
    __tag__ = ('p', 'Bibline')
    __cls__ = Source
    #<a name="Clark"></a>
    #</p>
    # <p class="Bibline"><span class="Author">Clark, Ross.</span> <span class="PubYear">1976.</span>
    # <span class="RefTitle"><i>Aspects of Proto-Polynesian syntax</i></span>
    # <span class="RefText">. Auckland: Linguistic Society of New Zealand.</span></p>
    # <p class="Bibline2">———. <span class="PubYear">2009.</span>
    # <span class="RefTitle"><i>*Leo tuai: A comparative lexical study of North and Central Vanuatu languages</i></span>
    # <span class="RefText">. Canberra: Pacific Linguistics. (PL 603).</span></p>
    # <p class="Bibline2">———. <span class="PubYear">2011.</span><span class="RefTitle">Birds</span>
    # <span class="RefText">. In Malcolm Ross, Andrew Pawley and Meredith Osmond, eds., <i>The lexicon of Proto Oceanic, the culture and environment of ancestral Oceanic society</i>, vol. 4: Animals: 271-370.</span>

    """
   <p class="Bibline2">———, <span class="Author">and Mary Kawena Pukui</span>
<a name="Elbert"></a>
 <span class="PubYear">1979.</span><span class="RefTitle"><i>Hawaiian grammar</i></span><span class="RefText">. Honolulu: The University Press of Hawaii.</span>
<a name="Elgincolin"></a>
</p> 
    """

    def __iter__(self):
        for html in self.iter_html():
            author = None
            for e in html.find_all(self.__tag__[0], class_=True):
                if e['class'][0] == 'Bibline':
                    res = Source(html=e)
                    author = res.author
                    yield res
                elif e['class'][0] == 'Bibline2':
                    assert author
                    yield self.__cls__(html=e, author=author, bibline2=True)


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
        return isinstance(e, Tag) and e.name == 'p' and e['class'][0] == 'setnote'

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
                    assert cls in (None, 'wd', 'pwd', 'lg', 'plg', 'bib', 'proto', 'note', 'fam'), str(c)
                ref = Ref.from_html(c)
                if ref:
                    self.refs.append(ref)
                    self.markdown += '[{}](bib-{})'.format(ref.label, ref.key)
                elif cls == 'note':
                    pass
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
                    #
                    # FIXME: turn language spans/links into markdown links
                    #
                    self.markdown += '[{}](lang-{})'.format(c.get_text(), c.get_text())
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
        self.plain = re.sub('\s+\(\)', '', self.plain)
        self.plain = self.plain.strip()
        self.markdown = self.markdown.strip()


@attr.s
class Set(Item):
    """
    <td class="entrytable">
        <p class="pidno">9625</p>
        <a name="saku₃"></a>
        <p class="pLang">
            <span class="pcode">POC</span> &nbsp; &nbsp;
            <span class="lineform">*saku₃ </span>
            <span class="linegloss"><a class="setline" href="acd-ak_k.htm#kind">kind </a> of  <a class="setline" href="acd-ak_b.htm#banana">banana</a> </span>
            #FIXME#
            <span class="dbl">[doublet: <a href="acd-s_t.htm#5496">*tabuRiq</a>]<span>
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
    id = attr.ib(default=None)  # pidno
    key = attr.ib(default=None)
    gloss = attr.ib(default=None)
    lookup = attr.ib(default=attr.Factory(list))
    proto_language = attr.ib(default=None)
    forms = attr.ib(default=attr.Factory(list))
    note = attr.ib(default=None)

    def __attrs_post_init__(self):
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
        self.key = lang.find('span', class_='lineform').text.strip()
        self.gloss = lang.find('span', class_='linegloss').get_text()
        pcode = lang.find('span', class_='pcode')
        if pcode:
            self.proto_language = pcode.get_text()


        name = None
        if forms:
            pnote = forms.find('p', class_='pnote')
            if pnote:
                self.note = Note.from_html(pnote)
            for tr in forms.find_all('tr'):
                if tr.find('td', class_='formuni'):
                    form = Form(html=tr, language=name)
                    self.forms.append(form)
                    name = form.language
        else:
            print('{} - no forms'.format(self.id))


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

        for e in self.html.find_all('p', class_='pidno'):
            self.sets.append(Set.from_html(e))
        #if self.formosan_only:
        #    print('F', self.id)


class EtymonParser(Parser):
    __glob__ = 'acd-s_*.htm'
    __cls__ = Etymon
    __tag__ = ('table', ('settable', 'SettableF'))  # tables class=entrytable + p class=setnote
    """
    <p class="setline">
      <span class="key">*tektek₁</span>
      <span class="setline">
        <a class="setline" href="acd-ak_c.htm#chopping">chopping </a>
        <a class="setline" href="acd-ak_t.htm#to">to </a>
        <a class="setline" href="acd-ak_p.htm#piece">pieces, </a>
        <a class="setline" href="acd-ak_c.htm#cutting">cutting </a>
        <a class="setline" href="acd-ak_u.htm#up"> up, </a>
        as
        <a class="setline" href="acd-ak_m.htm#meat">meat </a>
        <a class="setline" href="acd-ak_o.htm#or">or </a> <a class="setline" href="acd-ak_v.htm#vegetable">vegetables</a>
      </span>
    </p>
    <a name="8913"></a>
    <p></p><table class="entrytable"><tbody><tr><td class="entrytable">
    <p class="pidno">8913</p>
    <a name="tektek₁"></a><p class="pLang"><span class="pcode">PAN</span> &nbsp; &nbsp; <span class="lineform">*tektek₁ </span><span class="linegloss"><a class="setline" href="acd-ak_c.htm#chopping">chopping </a> <a class="setline" href="acd-ak_t.htm#to">to </a> <a class="setline" href="acd-ak_p.htm#piece">pieces, </a> <a class="setline" href="acd-ak_c.htm#cutting">cutting </a> <a class="setline" href="acd-ak_u.htm#up"> up, </a> as  <a class="setline" href="acd-ak_m.htm#meat">meat </a> <a class="setline" href="acd-ak_o.htm#or">or </a> <a class="setline" href="acd-ak_v.htm#vegetable">vegetables</a> </span>
    </p>
    <table class="forms" width="90%" align="center">
    <tbody><tr valign="top">
    <td class="group">Formosan</td></tr>
    <tr valign="top"><td class="lg"><a href="acd-l_S.htm#Saisiyat"><span class="lg">Saisiyat</span></a></td>
    <td class="formuni">təktək</td><td class="gloss">to chop wood</td></tr>
    <tr valign="top">

    <p class="setline"><span class="key">*-i₁</span> <span class="setline">imperative suffix</span></p>
    <a name="3033"></a>
    <p><table class="entrytable"><tbody><tr><td class="entrytable">
    <p class="pidno">3033</p>
    <a name="-i₁"></a><p class="pLang"><span class="pcode">PAN</span> &nbsp; &nbsp; <span class="lineform">*-i₁ </span><span class="linegloss">imperative suffix </span>
    <table class="forms" width="90%" align="center">
    <tbody><tr valign="top">
    <td class="group">Formosan</td></tr>
    <tr valign="top"><td class="lg">Atayal</td>
    <td class="formuni">-i</td><td class="gloss">suffix forming first passive negatable indicative and imperative from the reduced stem</td></tr>
    ...
    <p class="setnote"><span class="note">Note: &nbsp; </span><span class="bib"><a class="bib" href="acd-bib.htm#Egerod">Egerod (1965)</a></span> describes three "passives'' for <span class="lg">Atayal</span>: (1) a "relational passive'', (2) an "indefinite passive'', and (3) a "definite passive''.  The definite passive can occur in any of five aspects, of which the "neutral definite passive'' is marked by <span class="wd">-an</span>, while the "negatable neutral definite passive'' and the "imperative definite passive'' are marked by <span class="wd">-i</span>.  The paradigmatic alternation of <span class="wd">-an</span> and <span class="wd">-i</span> thus appears to be common to at least <span class="lg">Atayal</span> and <span class="lg">Bikol</span>.  The present affix evidently is identical to what <span class="bib"><a class="bib" href="acd-bib.htm#Wolff">Wolff (1973:73)</a></span> called the "local passive dependent'' construction. It seems to have marked imperatives of a certain type, but may have been used with a wider range of construction types than I have indicated here.
</p>
    """
    def __iter__(self):
        for html in self.iter_html():
            for e in html.find_all(self.__tag__[0], class_=self.__tag__[1]):
                yield self.__cls__.from_html(e)


def set_from_href(a):
    f, _, pid = a['href'].partition('#')
    return f.replace('acd-', '').replace('.htm', '').split('_')[0], pid


@attr.s(auto_detect=True)
class LForm(Item):
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
    form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    sets = attr.ib(default=attr.Factory(set))
    note = attr.ib(default=None)
    is_proto = attr.ib(default=False)

    is_root = attr.ib(default=False)
    ass = attr.ib(default=False)
    met = attr.ib(default=False)

    def __attrs_post_init__(self):
        link = self.html.find('a', href=True)
        self.href = link['href']
        self.form, self.note = form_and_note(link.text.strip())
        if self.form.startswith('*'):
            self.form = self.form[1:].strip()
        self.gloss = Gloss(self.html.find('span', class_='formdef'))

        for a in self.html.find_all('a', class_=True, href=True):
            if a['class'][0] == 'setkey' or a['class'][0].startswith('pform'):
                self.sets.add(set_from_href(a))
        if 'r' in {s[0] for s in self.sets}:
            self.is_root = True


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

    @property
    def is_proto(self):
        return self.name.startswith('Proto-')

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
            e = self.html.find('span', class_='ISO')
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
            form = next(forms)
            for f in forms:
                form.sets = form.sets.union(f.sets)
            dedup.append(form)

        self.forms = dedup
        if self.abbr:
            if self.abbr == self.name:
                self.abbr = None
            else:
                self.abbr = self.abbr.lower()


class LanguageParser(Parser):
    __glob__ = 'acd-l_*.htm'
    __cls__ = Language
    __tag__ = ('p', ('langline', 'dialpara'))

    def include(self, p):
        return (not p.stem.endswith('2')) and p.stem[-1].islower() #and ('plg' not in p.stem)


@attr.s
class Form(Item):
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
    form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    language = attr.ib(default=None)
    is_proto = attr.ib(default=False)
    is_root = attr.ib(default=False)
    set = attr.ib(default=None)
    bracketed = attr.ib(default=False)
    ass = attr.ib(default=False)
    met = attr.ib(default=False)
    note = attr.ib(default=None)

    def __attrs_post_init__(self):
        for e in self.html.find_all('span', class_='brax'):
            e.extract()
            self.bracketed = True
        self.gloss = Gloss(html=self.html.find('td', class_='gloss'))
        pform = self.html.find('td', class_='rootproto')
        if pform:
            lgcls = 'lgP'
            self.is_root = True
            self.form = pform.get_text()
            slink = pform.find('a', class_='rootproto')
            if slink:
                self.set = slink['href']
        else:
            lgcls = 'lg'
            formuni = self.html.find('td', class_='formuni')
            for cls in ['Met', 'Ass', 'hwnote']:
                o = formuni.find('span', class_=cls)
                if o:
                    setattr(self, cls.lower().replace('hw', ''), o.text if cls == 'hwnote' else True)
                    o.extract()

            self.form, _ = form_and_note(formuni.get_text().strip())
        lg = re.sub(r'\s+', ' ', self.html.find('td', class_=lgcls).text.strip())
        if lg:
            self.language = lg
        if self.language.startswith('Proto-'):
            self.is_proto = True
        if self.is_proto and self.form.startswith('*'):
            self.form = self.form[1:].strip()


@attr.s
class Root(Item):
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
    id = attr.ib(default=None)
    note = attr.ib(default=None)
    key = attr.ib(default=None)
    gloss = attr.ib(default=None)
    forms = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        self.note = Note.from_html(self.html.find('p', 'setnote'))
        self.id = int(self.html.find('p', class_='SetIdno').text)
        self.key = self.html.find('span', class_='key').text
        self.gloss = self.html.find('span', class_='key').get_text()

        name = None
        for tr in self.html.find('table', class_='formsR').find_all('tr'):
            if tr.find('td'):
                form = Form(html=tr, language=name)
                self.forms.append(form)
                name = form.language


class RootParser(Parser):
    __glob__ = 'acd-r_*.htm'
    __cls__ = Root
    __tag__ = ('table', 'settableR')


REFS = {
    "Ross 2006": ["Ross 2006a"],  # 6
    "Dempwolff 1938": ["Dempwolff 1934/38"],  # 5
    "Osmond and Ross 2016": ["Osmond and Ross 2016a", "Osmond and Ross 2016b"],  # 5
    "Blust n.d. 1975": ["Blust 1975b"],  # 3
    "Macdonald and Soenjono 1967": ["Macdonald and Darjowidjojo 1967"],  # 3
    "Madulid 1999": ["Madulid 2001"],  # 2
    "Fox, J. 1993": ["Fox 1993a"],  # 2
    "Lobel 2014": ["Lobel 2016"],  # 2
    "Pratt 1893": ["Pratt 1984"],  # 2
    "Jeng 1972": ["Jeng 1971"],  # 2
    "Jackson 1983": ["Jackson and Marck 1991"],  # 2
    "van Wouden 1968 [1935]": ["Van Wouden 1968"],  # 2
    "Warneck 1977 [1906]": ["Warneck 1977"],  # 2
    "Warneck 1906": ["Warneck 1977"],  # 2
    "Van der Veen 1940": ["van der Veen 1940"],  # 2
    "Gonda 1973 [1952]": ["Gonda 1973"],  # 2
    "Osmond and Pawley 2016a": [""],  # 2
    "Blust n.d. 1971": ["Blust 1971"],  # 1
    "Echols and Shadily": ["Echols and Shadily 1963"],  # 1
    "Wallace 1869 1962": ["Wallace 1962"],  # 1
    "Blust n.d. [1971]": ["Blust 1971"],  # 1
    "Bender et al 2003": ["Bender et al. 2003"],  # 1
    "Horne": ["Horne 1974"],  # 1
    "Madulid": ["Madulid 2001"],  # 1
    "Fox, C. 1970": ["Fox 1970"],  # 1
    "Collins n.d.": [""],  # 1
    "Ross n.d. b., Anastasia Vuluku Kaue from Makiri village, courtesy of Hiroko Sato": [""],  # 1
    "Tsuchida, Yamada and Moriguchi 1991": [""],  # 1
    "Freeman n.d.a.": [""],  # 1
    "Mintz and Britanico 1985": ["Mintz and del Rosario Britanico 1985"],  # 1
    "Blust n.d. [1975]": ["Blust 1975"],  # 1
    "Collins n.d. b": [""],  # 1
    "Reid 1976, Reid p.c.": ["Reid 1976"],  # 1
    "White 1985": [""],  # 1
    "Fox, J. n.d.": [""],  # 1
    "Hughes n.d.": [""],  # 1
    "Polillo Dumagat": [""],  # 1
    "Wallace 1869, Dick Teljeur, p.c.": [""],  # 1
    "Conklin 1953, Reid p.c.": ["Conklin 1953"],  # 1
    "Hohulin et al. 2018": ["Hohulin, Hohulin and Maddawat 2018"],  # 1
    "Rubino 2000, Carro 1956": ["Rubino 2000", "Carro 1956"],  # 1
    "Ruch n.d.": [""],  # 1
    "Esser 1964, Blust n.d. 1971": ["Esser 1964", "Blust 1971"],  # 1
    "Reid 1971, Hohulin et al 2018": ["Reid 1971", "Hohulin, Hohulin and Maddawat 2018"],  # 1
    "Rousseau n.d.": [""],  # 1
    "Walker 1975,1976": ["Walker 1976"],  # 1
    "Fox, C. 1974": [""],  # 1
    "van Dierendonck n.d.": [""],  # 1
    "Wallace 1962 [1869]": ["Wallace 1962"],  # 1
    "Chowning n.d. b": [""],  # 1
    "Fox, C. 1955": [""],  # 1
    "Warren 1959, Reid p.c.": ["Warren 1959"],  # 1
    "Hooley 1971, Adams and Lauck 1975": [""],  # 1
    "Allen and Beaso1975": [""],  # 1
    "Cauquelin 1991": [""],  # 1
    "Nivens": [""],  # 1
    "Bender et al. 2003, 2003a": [""],  # 1
    #"Elgincolin, Goschnick and Elgincolin 1988": [""],  # 1
    "Walker n.d.": [""],  # 1
    "Blust n.d. 1975b": [""],  # 1
    "Rajki 2018": [""],  # 1
    "Capell 1943, Ezard 1985": [""],  # 1
    "Beech 1908, Lobel 2016": [""],  # 1
    "Hostetler 1975": [""],  # 1
    "Schlegel 1971, Reid p.c.": [""],  # 1
    "Seeddon 1978": [""],  # 1
    "Melody Ross p.c.": [""],  # 1
    "Held 1942, Anceaux 1961": [""],  # 1
    "Holznecht 1989": [""],  # 1
    "Rau, Dong, et al. 2012, Tsuchida 1987": [""],  # 1
    "McFarland 1977, Davis and Mesa 2000": [""],  # 1
    "van der Miesen": [""],  # 1
    "Ogawa 1934": [""],  # 1
    "Adriani 1928, sub onta": [""],  # 1
    "Soenjono and Macdonald 1967": [""],  # 1
    "Panitia 1978": [""],  # 1
    "Ismail, Azis, Yakub, Taufik H. and Usman 1985": [""],  # 1
    "Laktaw": ["Laktaw 1914"],  # 1
    "Panganiban": ["Panganiban 1966"],  # 1
    "Panganiban1966": ["Panganiban 1966"],  # 1
    "van der Tuuk 1864/67": [""],  # 1
    "van der Tuuk 1971 [1864/67]": [""],  # 1
    "van Hasselt and van Hasselt 1947, sub nin": [""],  # 1
    "Tsuchida, Yamada, and Moriguchi 1987": [""],  # 1
    "Soeparno p.c.": [""],  # 1
    "Rau 2006": [""],  # 1
    "Conklin 1956": [""],  # 1
    "van Hoëvell 1877": [""],  # 1
    "Tylor 1958 [1871]": [""],  # 1
    #"Biggs, Walsh and Waqa 1970": [""],  # 1
    "Rau, Dong and Chang 2012": [""],  # 1
    "Blust 1972b, no. 55": [""],  # 1
    "Darlington 1957": [""],  # 1
    "Greenberg 1966": [""],  # 1
    "Smith n.d.": [""],  # 1
    "Pawley 1978": [""],  # 1
    "Li and Tsuchida 2006)": [""],  # 1
    "K.A. Adelaar": [""],  # 1
    "Dempwolff 1939": [""],  # 1
    #"Starosta, Pawley and Reid 1982": [""],  # 1
    "English 1985": [""],  # 1
    "Li n.d.": [""],  # 1
    #"Awed, Underwood and van Wynen 2004": [""],  # 1
    "Llamzon 1971": [""],  # 1
    "Ross 1996b": [""],  # 1
    "D.J. Prentice and James T. Collins": [""],  # 1
    "Ross 1998": [""],  # 1
    "Himes 2002": [""],  # 1
    "Lichtenberk and": [""],  # 1
    "1998": [""],  # 1
    "Pawley and Sayaba": [""],  # 1
    "Sagart 2004": [""],  # 1
    "Verheijen n.d.": [""],  # 1
    "Schapper 2011": [""],  # 1
    #"Osmond, Pawley and Ross 2003": [""],  # 1
    "J.N. Sneddon p.c.": [""],  # 1
    "Peterson 1931/51": [""],  # 1
    "Wolff 2010, 2": [""],  # 1
    "Chowning 1991": [""],  # 1
    "Blust 2013, Table 6.5": [""],  # 1
    "Dempwolff’s": [""],  # 1
    "Milke 9168": [""],  # 1
    "Madulid 2001.2": ["Madulid 2001"],  # 1
    "Blust 2002a": [""],  # 1
    "Arms 1973": [""],  # 1
    "Dempwoff 1938": [""],  # 1
    "Tsuchida": [""],  # 1
    "Darwin Voyage of the Beagle 1839": [""],  # 1
    "Blust 1970, fn. 123": [""],  # 1
    "Blust 1974, fn. 4": [""],  # 1
    "Pratt 1984 [1893]": [""],  # 1
    "Ivens 1927": [""],  # 1
    "Blust 2013, sect. 8.2.2.4": [""],  # 1
    "Pratt 1878": [""],  # 1
    "Zorc": [""],  # 1
    "Evans 2008": [""],  # 1
    "Blust 1998a, 2010a": [""],  # 1
    "Ross 2011": [""],  # 1
    "Pawley and Pawley 1994": [""],  # 1
    "Conant": [""],  # 1
    "Dahl 1978": [""],  # 1
    "Nihira 1983 [1932]": ["Nihira 1983"],  # 1
    "Zumbroich 2008": [""],  # 1
    "Mills 1973": [""],  # 1
    "Wolff 1971": [""],  # 1
    "Pratt 1984/1893": ["Pratt 1984"],  # 1
    "Blust 1980, no. 433": ["Blust 1980"],  # 1
    "Denmpwolff 1938": ["Dempwolff 1934/38"],  # 1
    "Pick, to appear": [""],  # 1
    "Blust 1981, 1991a": ["Blust 1981", "Blust 1991a"],  # 1
    "Blust 2015": [""],  # 1
    "Zorc n.d.": [""],  # 5
    "Geraghty n.d.": [""],  # 2
    "Li 2004": [""],  # 2
    "Chowning 2001": [""],
    # https://core.ac.uk/download/pdf/160609367.pdf#page=85 Proto Melanesian plant names reconsidered
    "Blust 2009": [""],  # 2
    "Dempwolff": [""],  # 1
    "Pigeaud": [""],  # 1
    "Zorc 1981": [""],  # 1
    "Fox n.d.": [""],  # 1
    "Grace n.d.": [""],  # 1
    "Fox 1993": [""],  # 1
    "Madulid 2000": [""],  # 1
    "Bergaño": [""],  # 1
    "Elkins and Hendrickson 1984": [""],  # 1
    "Blust n.d.": [""],  # 1
    "Collins n.d. a": [""],  # 1
    "Abo, Bender, Capelle and deBrum 1976": [""],  # 1
    "Ross n.d.": [""],  # 1
    "Collins n.d.a.": [""],  # 1
    "Gibson": [""],  # 1
    "Chinnery 1927": [""],  # 1
    "Capell": [""],  # 1
    "Bender et al 2003a": [""],  # 1
    "Rubino": [""],  # 1
    "Vanoverbergh 1956": [""],  # 1
    "Tuan": [""],  # 1
    "Evans 1923": [""],  # 1
    "Echols and Shadily 1965": [""],  # 1
    "Blust n.d": [""],  # 1
    "Smits and Voorhoeve 1992": [""],  # 1
    "Benton 1971a": [""],  # 1
    "Tsuchida1976": [""],  # 1
    "Jonker": [""],  # 1
    "Ferrell 1971": [""],  # 1
    "Pratt 1984 [1911]": [""],  # 1
    "Pratt": [""],  # 1
    "Churchill 1912": [""],  # 1
    "Fox, J. n.d": [""],  # 1
    "Lobel 2012": [""],  # 1
    "Blust, fieldnotes": [""],  # 1
    "Verheijen 1967": [""],  # 1
    "Stresemann 1927, van der Miesen 1911": [""],  # 1
    "Siregar 1977, Warren 1959": [""],  # 1
}

def clean_ref(ref):
    ref = ref.strip()
    if '(' in ref:
        author, _, rem = ref.partition('(')
        year, _, rem = rem.partition(')')
        year, _, pages = year.partition(':')
        ref = '{} {}'.format(author.strip(), year.strip())
    elif ':' in ref:
        ref, _, pages = ref.partition(':')
        ref = ref.strip()

    ref = normalize_years(ref)
    ref = ref.replace("’s ", ' ').replace("'s ", ' ').replace(', and ', ' and ')
    ref = {
        'Ross 2008':
            # There's Ross 2008a-g - all in the same collection
            'Ross, Pawley and Osmond 2008',
        'Ross 2003':
            # There's Ross 2003a-c - all in the same collection
            'Ross, Pawley and Osmond 2003',
        'Ross and Osmond 2016': 'Ross, Pawley and Osmond 2016',
        'Ross 2016a': 'Ross 2016',
        'Osmond 1998': 'Osmond and Ross 1998',
    }.get(ref, ref)
    ref = ref.strip()

    ref = REFS.get(ref, ref)
    if not isinstance(ref, list):
        ref = [ref]
    return ref


def main():
    sources = {}
    for src in SourceParser():
        #print(src.author)
        #print(src.key)
        #print(src.key)
        #if src.key in sources:
        #    raise ValueError(src.key)
        #if 'Osmond' in src.key:
        #    print(src.key)
        sources[src.key] = src

    refs = collections.Counter()
    langs = collections.OrderedDict()
    for lang in LanguageParser():
        for ref in lang.refs:
            #assert ref.key in sources, ref.key
            refs.update([ref.label])
        if lang.id in langs:
            # Proto-Western Micronesian is listed twice ...
            assert int(lang.id) == 19629
            assert lang.nwords == langs[lang.id].nwords
            langs[lang.id].abbr = 'pwmc'
            continue
        langs[lang.id] = lang
    assert len(langs) == len(set(l.name for l in langs.values())), 'duplicate language name'

    forms, linked_sets = set(), set()
    for l in langs.values():
        for form in l.forms:
            for ref in form.gloss.refs:
                #assert ref.key in sources, ref.key
                refs.update([ref.label])
            forms.add((l.name, form.form))
            for cat, no in form.sets:
                if cat in ['f', 's']:
                    linked_sets.add(int(no))

    forms_by_lang = {}
    for l in langs.values():
        forms_by_lang[l.name] = {(f.form, f.gloss.plain): f for f in l.forms}
    for l in langs.values():
        if l.abbr and l.abbr not in forms_by_lang:
            forms_by_lang[l.abbr] = forms_by_lang[l.name]

    for w in WordParser():
        if w.language == 'Kaniet (Thilenius)':
            continue
        assert (w.language in forms_by_lang) or (w.language.lower() in forms_by_lang), w.language
        form = w.headword
        if w.note:
            form = '{} ({})'.format(form, w.note)
        forms = forms_by_lang.get(w.language, forms_by_lang.get(w.language.lower()))
        assert (form, w.gloss.plain) in forms, '{}: "{}" {}'.format(w.language, form, w.gloss.plain)

    sets, etyma = set(), collections.defaultdict(set)
    for e in EtymonParser():
        if e.note:
            for ref in e.note.refs:
                refs.update([ref.label])
        for s in e.sets:
            if s.note:
                for ref in s.note.refs:
                    refs.update([ref.label])
            etyma[e.id].add(s.id)
            if s.id in sets:
                raise ValueError(s.id)
            sets.add(s.id)
            for f in s.forms:
                if f.language == 'Kaniet (Thilenius)':
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

    #assert len(linked_sets - sets) < 30
    #print(len(sets - linked_sets), 'sets not linked from language forms')
    #print(len(sets.intersection(linked_sets)), 'sets linked from language forms')
    #print(list(sets - linked_sets)[:30])

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
    for k, v in refs.most_common():
        print(k, v)
    return

    for s in RootParser():
        if s.note and s.note.plain:
            print(s.note.markdown)


if __name__ == '__main__':
    main()
