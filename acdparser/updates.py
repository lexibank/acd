import re
import zipfile
import itertools

from lxml import etree

NS = dict(
    text="urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    style="urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    xlink="http://www.w3.org/1999/xlink",
    fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
)
LNAMES = {
    'Ayta Abellen': 'Ayta Abellan',
    'Waray': 'Waray-Waray',
}


def qname(prefix, lname):
    return '{%s}%s' % (NS[prefix], lname)


def compute_indentation(props):
    """
    Compute the indentation in inches from the properties of a paragraph style.
    """
    res = 0
    for k, v in props.items():
        if k in ['margin-left', 'text-indent']:
            try:
                res += float(v.replace('in', ''))
            except:
                pass
    return res


def transform(e, styles):
    """
    We use XSLT to
    - replace <text:tab/> tags the text `"___tab___"`
    - replace <text:span> tags with italic or bold styles with the corresponding markdown formatting
    """
    tmpl = """<xsl:template match="text:span[@text:style-name='{0}']">{1}<xsl:apply-templates select="node()" />{1}</xsl:template>"""
    templates = []
    for name, props in styles.items():
        if props.get('font-style') == 'italic':
            templates.append(tmpl.format(name, '_'))
        elif props.get('font-weight') == 'bold':
            templates.append(tmpl.format(name, '__'))

    xslt="""\
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" {}> 
    <xsl:template match="text:tab">___tab___</xsl:template>
{}
    <xsl:template match="*">
        <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
    </xsl:template>
    <xsl:template match="@*|text()|comment()|processing-instruction">
        <xsl:copy-of select="."/>
    </xsl:template>
</xsl:stylesheet>
""".format(' '.join('xmlns:{}="{}"'.format(k, v) for k, v in NS.items()), '\n'.join(templates))
    return etree.XSLT(etree.fromstring(xslt.encode('utf8')))(e)


def get_styles(d):
    """
    Read text and paragraph styles from the document.
    """
    res = dict(text=dict(), paragraph=dict())
    for style in d.xpath('.//style:style', namespaces=NS):
        for prop in style.xpath('style:text-properties', namespaces=NS):
            res['text'][style.get(qname('style', 'name'))] = {k.split('}')[1]: v for k, v in prop.attrib.items()}
        for prop in style.xpath('style:paragraph-properties', namespaces=NS):
            res['paragraph'][style.get(qname('style', 'name'))] = {k.split('}')[1]: v for k, v in prop.attrib.items()}
    return res


def splitline(indent, text):
    res = []
    in_margin = True

    for s in text.split('___tab___'):
        s = s.strip()
        if re.fullmatch(r'\([a-c]\)', s):  # strip "(a)", "(b)"-type ordering of witnesses.
            s = ''
        if not s:
            if in_margin:  # Leading tabs contribute to the indentation.
                indent += 0.5
            continue
        else:
            in_margin = False
            # Sometimes the tabs are wrapped in spans and thus styled. We detect this by
            # checking for trailing or leading markdown markup of the tab-separated chunks.
            for markup in ['__', '_']:
                if s.startswith(markup) and markup not in s[len(markup):]:
                    s = s.replace(markup, '')
                elif s.endswith(markup) and markup not in s[:-len(markup)]:
                    s = s.replace(markup, '')
            s = s.replace('__ __', '')
            if s:
              res.append(s)
    return indent, res


def parse(p, verbose=False):
    doc = get_content(p)
    styles = get_styles(doc)
    doc = transform(doc, styles['text'])
    indentation = {name: compute_indentation(props) for name, props in styles['paragraph'].items()}
    lines = [
        splitline(indentation.get(p.get(qname('text', 'style-name')), 0), ''.join(p.itertext()))
        for p in doc.xpath('.//text:p', namespaces=NS)]

    yield from iter_etyma(lines)

    if verbose:
        for e, w, n in iter_etyma(lines):
            print(len(w))
            #
            # FIXME: Create Etymon object instances, ready for saving as JSON
            #
            print('{}\t{}\t{}'.format(*e))
            for sg, items in itertools.groupby(w, lambda i: i[0]):
                print(sg)
                for lg, forms in itertools.groupby(items, lambda i: i[1]):
                    print('***', lg)
                    for i, (_, _, form, gloss) in enumerate(forms):
                        if i == 0:
                            print('{}\t{}\t{}'.format(lg, form, gloss))
                        else:
                            print('\t{}\t{}'.format(form, gloss))
            if n:
                print()
                print('NOTE: {}'.format(n))
            print('============================================')


def get_content(p):
    with zipfile.ZipFile(p) as z:
        with z.open('content.xml') as fp:
            return etree.fromstring(fp.read())


def iter_etyma(lines):
    etymon, note, subgroup, witnesses = None, None, None, []
    lnamestart = None

    for indent, line in lines:
        if line and line[0].startswith('UPGRADES'):
            #
            # FIXME: learn to parse upgrades/fixes
            #
            break
        #print(indent, line)
        if not line:  # empty lines are not informative
            continue
        if len(line) == 1 and set(list(line[0])) == {'='}:  # explicit etymon separator
            if etymon:
                yield etymon, witnesses, note
            etymon, note, subgroup, witnesses = None, None, None, []
            continue

        if len(line) > 1 and re.fullmatch('P[A-Zh]+', line[0]):  # new etymon start
            line[0] = line[0].upper()
            if etymon:
                yield etymon, witnesses, note
            if len(line) == 2:  # Fix missing separation of proto-form and gloss.
                formplus = line[1].split()
                line = [line[0]] + [formplus[0], ' '.join(formplus[1:])]
            etymon = line
            note, subgroup, witnesses = None, None, []
            continue

        if etymon:
            if len(line) == 1:
                if re.fullmatch('[A-Z]+', line[0]):  # A subgroup line.
                    subgroup = line[0].upper()
                elif note:  # We are already in the note, so assume this is a continuation line.
                    note += ' ' + line[0]
                elif line[0].startswith('NOTE:'):  # Note starts here.
                    note = line[0].replace('NOTE:', '').strip()
                else:
                    if indent < 2:
                        # A single item on a line with small indentation: Assume this is the first
                        # part of a long language name.
                        lnamestart = line[0]
                    else:
                        # A single item on a line with big indentation: Assume this is a
                        # continuation line for a long gloss.
                        witnesses[-1][-1] += ' ' + line[0]
            elif 3 <= len(line) <= 4:  # A proper witness line, giving language name, form and gloss.
                lname = line[0]
                if lnamestart:
                    lname = '{} {}'.format(lnamestart, lname)
                    lnamestart = None
                lname = LNAMES.get(lname, lname)
                witnesses.append([subgroup, lname, line[1], ' '.join(line[2:])])
            else:
                assert len(line) == 2 and 1 < indent < 3, line
                # A two-item line. Assume this is another (form, gloss) pair for the language of
                # the last language.
                witnesses.append([subgroup, witnesses[-1][1], line[0], line[1]])

    if witnesses:
        yield etymon, witnesses, note


#if __name__ == '__main__':
#    import sys
#    parse(sys.argv[1])
