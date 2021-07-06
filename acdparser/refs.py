from .util import normalize_years

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
    ref, pages = ref.strip(), ''
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
    return [(r, pages.strip()) for r in ref]
