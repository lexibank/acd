import re
import itertools

from bs4 import BeautifulSoup as bs

from .models import *

__all__ = ['SourceParser', 'LanguageParser', 'WordParser', 'EtymonParser']


class Parser:
    """
    A Parser is concerned with one main data type. As such it knows
    - how to select appropriate HTML input files
    - how to iterate over suitable HTML chunks, encoding the data of an object instance.
    """
    __tag__ = (None, None)
    __cls__ = None
    __glob__ = 'acd-*.htm'

    def __init__(self, d):
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


class WordParser(Parser):
    __glob__ = 'acd-w_*.htm'
    __cls__ = Word
    __tag__ = ('p', 'formline')


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


class LanguageParser(Parser):
    __glob__ = 'acd-l_*.htm'
    __cls__ = Language
    __tag__ = ('p', ('langline', 'dialpara'))

    def include(self, p):
        return (not p.stem.endswith('2')) and p.stem[-1].islower() #and ('plg' not in p.stem)


class RootParser(Parser):
    __glob__ = 'acd-r_*.htm'
    __cls__ = Root
    __tag__ = ('table', 'settableR')
