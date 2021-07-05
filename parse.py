import re
import pathlib
import itertools
import collections

import attr
import lxml
import cchardet
from bs4 import BeautifulSoup as bs, NavigableString, Tag


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
            (r'</\wd>', '</span>'),
            (r'<pkg>', '<span>'),
            ('t<m>alam', '<span class="wd">talam</span>'),
            ('</span><a> ', '</span></a> '),
            ('<p class="pnote"><hr><p class="pnote">', '<p class="pnote"'),
        ]:
            s = s.replace(src, t)
        return s

    def iter_html(self):
        for p in self.paths:
            if self.include(p):
                print(p)
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
    key = attr.ib(default=None)
    label = attr.ib(default=None)

    @classmethod
    def match(cls, e):
        return isinstance(e, Tag) and e.name == 'span' and \
            ('class' in e.attrs) and e['class'][0] == 'bib'

    def __attrs_post_init__(self):
        link = self.html.find('a')
        self.key = link['href'].split('#')[1]
        self.label = link.text


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
        self.plain = re.sub('\s+\(\)', '', self.plain.strip())


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
        if self.language in ['PRuk', 'PAty']:
            # In two cases, proto words are not marked up correctly:
            self.is_proto = True
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
    year = attr.ib(default=None)
    title = attr.ib(default=None)
    text = attr.ib(default=None)

    def __attrs_post_init__(self):
        for cls, attrib in [
            ('Author', 'author'),
            ('PubYear', 'year'),
            ('RefTitle', 'title'),
            ('RefText', 'text'),
        ]:
            e = self.html.find('span', class_=cls)
            if e:
                setattr(self, attrib, e.get_text())


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
                    yield self.__cls__(html=e, author=author)


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


def next_tag(e):
    n = e.next_sibling
    if n is None:
        return
    while not isinstance(n, Tag):
        n = n.next_sibling
        if n is None:
            return
    return n


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
    """
    href = attr.ib(default=None)
    form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    sets = attr.ib(default=attr.Factory(set))

    def __attrs_post_init__(self):
        link = self.html.find('a', href=True)
        self.href = link['href']
        self.form = link.text.strip()

        self.gloss = Gloss(self.html.find('span', class_='formdef'))

        for a in self.html.find_all('a', class_=True, href=True):
            if a['class'][0] == 'setkey' or a['class'][0].startswith('pform'):
                self.sets.add(set_from_href(a))


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

    def __attrs_post_init__(self):
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
        while (len(self.forms) < self.nwords) or (form and form.name == 'p' and form['class'][0] == 'formline'):
            if form is None or form.name != 'p':
                break
            if form['class'][0] == 'lbreak':
                form = next_tag(form)
            if form.name != 'p':
                break
            try:
                assert form['class'][0] == 'formline'
            except:
                print(form['class'])
                raise
            self.forms.append(LForm.from_html(form))
            form = next_tag(form)

        assert len(self.forms) >= self.nwords
        if len(self.forms) > self.nwords:
            print('+++', self.name)
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
    """
    form = attr.ib(default=None)
    gloss = attr.ib(default=None)
    language = attr.ib(default=None)
    is_proto = attr.ib(default=False)
    set = attr.ib(default=None)
    bracketed = attr.ib(default=False)
    ass = attr.ib(default=False)
    met = attr.ib(default=False)

    def __attrs_post_init__(self):
        for e in self.html.find_all('span', class_='brax'):
            e.extract()
            self.bracketed = True
        self.gloss = Gloss(html=self.html.find('td', class_='gloss'))
        pform = self.html.find('td', class_='rootproto')
        if pform:
            lgcls = 'lgP'
            self.is_proto = True
            self.form = pform.get_text()
            slink = pform.find('a', class_='rootproto')
            if slink:
                self.set = slink['href']
        else:
            lgcls = 'lg'
            formuni = self.html.find('td', class_='formuni')
            for cls in ['Met', 'Ass']:
                o = formuni.find('span', class_=cls)
                if o:
                    setattr(self, cls.lower(), True)
                    o.extract()

            self.form = formuni.get_text().strip()
        lg = re.sub(r'\s+', ' ', self.html.find('td', class_=lgcls).text.strip())
        if lg:
            self.language = lg


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


def main():
    langs = collections.OrderedDict()
    for lang in LanguageParser():
        if lang.id in langs:
            # Proto-Western Micronesian is listed twice ...
            assert int(lang.id) == 19629
            assert lang.nwords == langs[lang.id].nwords
            continue
        langs[lang.id] = lang
    assert len(langs) == len(set(l.name for l in langs.values())), 'duplicate language name'

    forms, sets = set(), set()
    for l in langs.values():
        for form in l.forms:
            forms.add((l.name, form.form))
            for cat, no in form.sets:
                if cat in ['f', 's']:
                    sets.add(int(no))

    langs = {l.name: set((f.form, f.gloss.plain) for f in l.forms) for l in langs.values()}

    c = 0
    existing = collections.Counter()
    seen = set()
    for e in EtymonParser():
        seen.add(e.id)
        for s in e.sets:
            if s.id in seen:
                raise ValueError(s.id)
            seen.add(s.id)
            for f in s.forms:
                if f.language == 'Kaniet (Thilenius)':
                    continue
                assert f.language in langs, f.language
                if (f.form, f.gloss.plain) not in langs[f.language]:
                    c += 1
                    print(f.language, f.form, f.gloss.plain)
                existing.update([(False, f.language)])

    assert len(sets - seen) < 30
    print(len(seen - sets), 'sets not linked from language forms')
    print(len(seen.intersection(sets)), 'sets linked from language forms')
    print(list(seen - sets)[:30])
    print(c)

    #for w in WordParser():
    #    if (w.language not in langs) and not w.is_proto:
    #        missing.update([w.language])
    #    else:
    #        existing.update([(w.is_proto, w.language)])
    #print(sum(1 for p, l in existing if not p), len(existing))
    #print(sum(v for k, v in existing.items() if not k[0]), sum(existing.values()))

    return

    for s in RootParser():
        if s.note and s.note.plain:
            print(s.note.markdown)

    for s in SetParser():
        if s.note and s.note.plain:
            print(s.note.markdown)

    return

    sources = list(SourceParser())
    print(len(sources), 'sources')

    data = collections.defaultdict(lambda: collections.defaultdict(list))
    bib = collections.Counter()
    stats = collections.Counter()
    cogsets = set()
    c = 0
    for w in WordParser():
        c += 1
        stats.update(['proto' if w.is_proto else 'word'])
        data[w.group][w.language].append(w)
        bib.update([r.key for r in w.gloss.refs])
        if w.cognateset:
            cogsets.add(tuple(list(w.cognateset)[:2]))
    print(c)

    sets = []
    for s in SetParser():
        sets.append(s)
    print(len(sets))

    #for m, l in sorted(cogsets):
    #    print('acd-{}_{}.htm'.format(m, l))

    print(stats)

    #for k in data:
    #    print(k, len(data[k]))

    #for k, v in bib.most_common():
    #    print(k, v)


if __name__ == '__main__':
    main()
