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


class EtymonParser(Parser):
    __glob__ = 'acd-s_*.htm'
    __cls__ = Etymon
    __tag__ = ('table', ('settable', 'SettableF'))  # tables class=entrytable + p class=setnote


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
