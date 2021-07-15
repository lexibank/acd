import re
import itertools

from bs4 import BeautifulSoup as bs

from .models import *

__all__ = ['SourceParser', 'LanguageParser', 'WordParser', 'EtymonParser', 'LoanParser',
           'NoiseParser', 'NearParser']


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
            ('<famg>', '<span class="fam">'),
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
        seen = set()
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
                    oid = getattr(o, 'id', None)
                    if not oid or (oid not in seen):
                        yield o
                    seen.add(oid)


class EtymonParser(Parser):
    __glob__ = 'acd-s_*.htm'
    __cls__ = Etymon
    __tag__ = ('table', ('settable', 'SettableF'))  # tables class=entrytable + p class=setnote


class NearParser(Parser):
    """
    These are comparisons in which the observed similarity appears too great to attribute to
    chance, but because of imprecise agreement the reconstruction of a well-defined form is not
    yet possible. In some cases these may be reflexes of doublets that have not yet been posited,
    or of morphemes that share a common monosyllabic root. Further comparative work may therefore
    lead to the transformation of some near comparisons into reconstructions with irregular
    material added in a note.
    """
    __glob__ = 'acd-near.htm'
    __cls__ = Near
    __tag__ = ('table', 'settableNear')

    def __iter__(self):
        for obj in Parser.__iter__(self):
            if obj.id not in [30320]:
                # some form sets are listed as loan and as near! On the language pages
                # forms are linked to Loan, though, so we skip them here.
                yield obj


class NoiseParser(Parser):
    """
    I have included a separate module of the dictionary called ‘Noise’ (in the
    information-theoretic sense of meaningless data that can be confused with a true signal).
    The reason for this is that the search process that results in valid cognate sets inevitably
    turns up other material that is superficially appealing, but is questionable for various
    reasons. To simply dispose of this ‘information refuse’ would be unwise for two reasons.
    First, further searching might show that some of these questionable comparisons are more
    strongly supported than it initially appeared. Second, even if the material is not upgraded
    through further comparative work it is always possible that some future researcher with
    different standards of evaluation will stumble upon some of these comparisons and claim that
    they are valid, but were overlooked in the ACD. By including a module on ‘Noise’ I can show
    that I have considered and rejected various possibilities that might be entertained by others.
    """
    __glob__ = 'acd-n_*.htm'
    __cls__ = Noise
    __tag__ = ('table', 'settableNoise')


class LoanParser(Parser):
    """
    Loanwords are a perennial problem in historical linguistics. When they involve morphemes that
    are borrowed between related languages they can provoke questions about the regularity of sound
    correspondences. When they involve morphemes that are borrowed between unrelated languages they
    can give rise to invalid reconstructions. Dempwolff (1934-38) included a number of known
    loanwords among his 2,216 ‘Proto-Austronesian’ reconstructions in order to show that sound
    correspondences are often regular even with loanwords that are borrowed relatively early, but
    he marked these with an ‘x’, as with *xbazu ‘shirt’, which he knew to be a Persian loanword in
    many of the languages of western Indonesia, and (via Malay) in some of the languages of the
    Philippines. However, he overlooked a number of cases, such as *nanas ‘pineapple’ (an Amazonian
    cultigen that was introduced to insular Southeast Asia by the Portuguese). Since widely
    distributed loanwords can easily be confused with native forms I have found it useful to
    include them in a separate module of the dictionary.

    A fairly careful (but inevitably imperfect) attempt has been made to identify and document
    loanwords with a distribution sufficient to justify a reconstruction on one of the eight levels
    of the ACD, if treated erroneously as native. While this has been done wherever the possibility
    of confusion with native forms seemed real, there is no reason to include obvious loans that
    would never be mistaken for native forms.

    This issue is especially evident in the Philippines, where hundreds of Spanish loanwords from
    the colonial period that began late in the 16th century, are scattered from at least Ilokano in
    northern Luzon to the Bisayan languages of the central Philippines and some of the languages of
    Mindanao (as Subanon). Comparisons like Ilokano kamarón ‘prawn’, Cebuano kamarún ‘dish of
    shrimps, split and dipped in eggs, optionally mixed with ground meat’ < Spanish camarón
    ‘shrimp’, or Ilokano kalábus ‘jail, prison’, Cebuano kalabús, kalabúsu ‘jail; to land in
    prison, in jail’ < Spanish calabozo ‘dungeon’ seem inappropriate for inclusion in LOANS, but
    introduced plants have generally been admitted. Some of these, as ‘tomato’ may be widely known
    as New World plants that were introduced to the Philippines by the Spanish, but others, as
    ‘chayote’, may be less familiar. As already noted, Dempwolff (1938) posited
    ‘Uraustronesisch’ *nanas and *kenas as doublets for ‘pineapple’, completely overlooking the
    fact that this is an Amazonian plant that could hardly have been present in the Austronesian
    world before the advent of the colonial period. This example shows that errors in the semantic
    domain of plant names can sometimes escape detection by scholars who are otherwise known for
    their careful, meticulous work, and for this reason all borrowed cognate sets involving plant
    names are documented as loanwords to avoid any possible misinterpretation.
    """
    __glob__ = 'acd-lo_*.htm'
    __cls__ = Loan
    __tag__ = ('table', 'settableLoan')

    def include(self, p):
        return ' ' not in p.stem


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
