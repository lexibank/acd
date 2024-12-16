<a name="ds-cldfmetadatajson"> </a>

# Wordlist Austronesian Comparative Dictionary

**CLDF Metadata**: [cldf-metadata.json](./cldf-metadata.json)

**Sources**: [sources.bib](./sources.bib)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Wordlist](http://cldf.clld.org/v1.0/terms.rdf#Wordlist)
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by/4.0/
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/lexibank/acd
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/lexibank/acd/tree/73a584a">lexibank/acd v1.2-31-g73a584a</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v5.1">Glottolog v5.1</a></li><li><a href="https://github.com/concepticon/concepticon-data/tree/v3.2.0">Concepticon v3.2.0</a></li><li><a href="https://github.com/cldf-clts/clts/tree/v2.3.0">CLTS v2.3.0</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>lingpy-rcParams</strong>: <a href="./lingpy-rcParams.json">lingpy-rcParams.json</a></li><li><strong>python</strong>: 3.12.3</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | acd
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-formscsv"></a>Table [forms.csv](./forms.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF FormTable](http://cldf.clld.org/v1.0/terms.rdf#FormTable)
[dc:extent](http://purl.org/dc/terms/extent) | 146733


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Local_ID](http://purl.org/dc/terms/identifier) | `string` | 
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | References [parameters.csv::ID](#table-parameterscsv)
[Value](http://cldf.clld.org/v1.0/terms.rdf#value) | `string` | 
[Form](http://cldf.clld.org/v1.0/terms.rdf#form) | `string` | 
[Segments](http://cldf.clld.org/v1.0/terms.rdf#segments) | list of `string` (separated by ` `) | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Cognacy` | `string` | 
`Loan` | `boolean` | 
`Graphemes` | `string` | 
`Profile` | `string` | 
[Description](http://clld.org/v1.0/terms.rdf#description) | `string` | Description of the meaning of the word (possibly in language-specific terms).
`Sic` | `boolean` | For a form that differs from the expected reflex in some way this flag asserts that a copying mistake has not occurred.

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1064


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string` | 
`Glottolog_Name` | `string` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal`<br>&ge; -90<br>&le; 90 | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal`<br>&ge; -180<br>&le; 180 | 
`Family` | `string` | 
`Abbr` | `string` | Abbreviation for the (proto-)language name.
`Group` | `string`<br>Regex: `PAN|Form.|PMP|PWMP|PPH|PCEMP|PCMP|PEMP|PSHWNG|POC` | Etymological dictionaries often operate with an assumed internal classification. This column lists such groups.
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | Etymological (or comparative) dictionaries typically compare lexical data from many source dictionaries.<br>References [sources.bib::BibTeX-key](./sources.bib)
`Is_Proto` | `boolean` | Specifies whether a language is a proto-language (and thus its forms reconstructed proto-forms).
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | For proto-languages that correspond to ACD reconstruction levels, a description of their extent is provided.
`Dialect_Of` | `string` | References [languages.csv::ID](#table-languagescsv)

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 86502


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Concepticon_ID](http://cldf.clld.org/v1.0/terms.rdf#concepticonReference) | `string` | 
`Concepticon_Gloss` | `string` | 

## <a name="table-cognatescsv"></a>Table [cognates.csv](./cognates.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CognateTable](http://cldf.clld.org/v1.0/terms.rdf#CognateTable)
[dc:extent](http://purl.org/dc/terms/extent) | 121682


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | References [forms.csv::ID](#table-formscsv)
[Form](http://linguistics-ontology.org/gold/2010/FormUnit) | `string` | 
[Cognateset_ID](http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference) | `string` | References [cognatesets.csv::ID](#table-cognatesetscsv)
`Doubt` | `boolean` | 
`Cognate_Detection_Method` | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Alignment](http://cldf.clld.org/v1.0/terms.rdf#alignment) | list of `string` (separated by ` `) | 
`Alignment_Method` | `string` | 
`Alignment_Source` | `string` | 
`Metathesis` | `boolean` | Flag indicating that a process of metathesis is assumed, explaining the apparent irregularity of a cognate.
`Assimilation` | `boolean` | Flag indicating that a process of assimilation is assumed, explaining the apparent irregularity of a cognate.
`Doublet_Comment` | `string` | A comment about the doublet status of the reconstruction.
`Doublet_Set` | `string` | Identifier of a set of variants that are independently supported by the comparative evidence. Doubletting that cannot be traced in any clear way to borrowing is extremely common in AN languages (Blust 2011), and an effort has been made to cross-reference doublets in the ACD wherever possible.
`Disjunct_Comment` | `string` | A comment about the disjunct status of the reconstruction.
`Disjunct_Set` | `string` | Identifier of a set of variants that are supported only by allowing the overlap of cognate sets; i.e. only one reconstruction in a set of disjuncts can be consistent with the evidence, but it is unclear which one. A distinction is drawn between doublets (variants that are independently supported by the comparative evidence), and “disjuncts” (variants that are supported only by allowing the overlap of cognate sets). To illustrate, both Tagalog gumí ‘beard’ and Malay kumis ‘moustache’ show regular correspondences with Fijian kumi ‘the chin or beard’, but they do not correspond regularly with one another. Based on this evidence, it is impossible to posit doublets, since unambiguous support for both variants is lacking. However, since the Tagalog and Malay forms can each be compared with Fijian kumi, two comparisons can be proposed that overlap by including the Fijian form in both (like all Oceanic languages, Fijian has merged PMP *k and *g; in addition, it has lost final consonants) . The result is a pair of PMP disjuncts *gumi (based on Tagalog and Fijian) and *kumis (based on Malay and Fijian), either or both of which could be used to justify an independent doublet if additional comparative support is found.

## <a name="table-cognatesetscsv"></a>Table [cognatesets.csv](./cognatesets.csv)

Comparisons with regular sound correspondences and close semantics. If there are additional forms that are strikingly similar but irregular, or that show strong semantic divergence, these are are added in a note. Every attempt is made to keep the comparison proper free from problems.

Because many reconstructed morphemes contain smaller submorphemic sound-meaning associations of the type that Brandstetter (1916) called ‘roots’ (Wurzeln), these elements are listed as cognate sets, too. They are marked with a true value for the 'Is_Root' property of the linked, reconstructed form.

The roots listed here thus amount to a continuation of the data set presented in Blust 1988.

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CognatesetTable](http://cldf.clld.org/v1.0/terms.rdf#CognatesetTable)
[dc:extent](http://purl.org/dc/terms/extent) | 10857


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | A recognizable label for the cognateset, typically the reconstructed proto-form and the reconstructed meaning.
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | Links to the reconstructed proto-form in FormTable.<br>References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Doubt` | `boolean` | Flag indicating (un)certainty of the reconstruction.
`Etymon_ID` | `string` | References [etyma.csv::ID](#table-etymacsv)
`Is_Main_Entry` | `boolean` | 

## <a name="table-cfcsv"></a>Table [cf.csv](./cf.csv)

The ACD includes five additional categories of groups of forms, called 'near cognates', 'noise', 'roots', 'loans' and 'also'. These are marked with respective values in the 'Category' column.

'Near cognates' are forms that are strikingly similar but irregular, and which cannot be included in a note to an established reconstruction. Stated differently, these are forms that appear to be historically related, but do not yet permit a reconstruction.

The 'noise' (in the information-theoretic sense of meaningless data that can be confused with a true signal) category lists chance resemblances. Given the number of languages being compared and the number of forms in many of the sources, forms that resemble one another in shape and meaning by chance will not be uncommon, and the decision as to whether a comparison that appears good is a product of chance must be based on criteria such as
- how general the semantic category of the form is (e.g. phonologically corresponding forms meaning ‘cut’ are less diagnostic of relationship than phonologically corresponding forms for particular types of cutting),
- how richly attested the form is (if it is found in just two witnesses the likelihood that it is a product of chance is greatly increased),
- there is already a well-established reconstruction for the same meaning.

Thus, the search process that results in valid cognate sets inevitably turns up other material that is superficially appealing, but is questionable for various reasons. To simply dispose of this ‘information refuse’ would be unwise for two reasons. First, further searching might show that some of these questionable comparisons are more strongly supported than it initially appeared. Second, even if the material is not upgraded through further comparative work it is always possible that some future researcher with different standards of evaluation will stumble upon some of these comparisons and claim that they are valid, but were overlooked in the ACD. By including a module on ‘Noise’ we can show that we have considered and rejected various possibilities that might be entertained by others.

Because many reconstructed morphemes contain smaller submorphemic sound-meaning associations of the type that Brandstetter (1916) called ‘roots’ (Wurzeln), these elements are included in the 'roots' category. The roots listed here thus amount to a continuation of the data set presented in Blust 1988.

Roots are not listed as regular cognate sets, because the reconstructions are not explicitly assigned to a proto-language.

Loanwords are a perennial problem in historical linguistics. When they involve morphemes that are borrowed between related languages they can provoke questions about the regularity of sound correspondences. When they involve morphemes that are borrowed between unrelated languages they can give rise to invalid reconstructions. Dempwolff (1934-38) included a number of known loanwords among his 2,216 ‘Proto-Austronesian’ reconstructions in order to show that sound correspondences are often regular even with loanwords that are borrowed relatively early, but he marked these with an ‘x’, as with *xbazu ‘shirt’, which he knew to be a Persian loanword in many of the languages of western Indonesia, and (via Malay) in some of the languages of the Philippines. However, he overlooked a number of cases, such as *nanas ‘pineapple’ (an Amazonian cultigen that was introduced to insular Southeast Asia by the Portuguese). Since widely distributed loanwords can easily be confused with native forms it is useful to include them in the dictionary.

A fairly careful (but inevitably imperfect) attempt has been made to identify and document loanwords with a distribution sufficient to justify a reconstruction on one of the nine levels of the ACD, if treated erroneously as native. While this has been done wherever the possibility of confusion with native forms seemed real, there is no reason to include obvious loans that would never be mistaken for native forms.

This issue is especially evident in the Philippines, where hundreds of Spanish loanwords from the colonial period that began late in the 16th century, are scattered from at least Ilokano in northern Luzon to the Bisayan languages of the central Philippines and some of the languages of Mindanao (as Subanon). Comparisons like Ilokano kamarón ‘prawn’, Cebuano kamarún ‘dish of shrimps, split and dipped in eggs, optionally mixed with ground meat’ < Spanish camarón ‘shrimp’, or Ilokano kalábus ‘jail, prison’, Cebuano kalabús, kalabúsu ‘jail; to land in prison, in jail’ < Spanish calabozo ‘dungeon’ seem inappropriate for inclusion in LOANS, but introduced plants have generally been admitted. Some of these, as ‘tomato’ may be widely known as New World plants that were introduced to the Philippines by the Spanish, but others, as ‘chayote’, may be less familiar. As already noted, Dempwolff (1938) posited ‘Uraustronesisch’ *nanas and *kenas as doublets for ‘pineapple’, completely overlooking the fact that this is an Amazonian plant that could hardly have been present in the Austronesian world before the advent of the colonial period. This example shows that errors in the semantic domain of plant names can sometimes escape detection by scholars who are otherwise known for their careful, meticulous work, and for this reason all borrowed cognate sets involving plant names are documented as loanwords to avoid any possible misinterpretation.

The last category, 'also', groups forms related to a particular cognate set. These forms typically show some kind of irregularity with respect to the proposed reconstruction, but provide context to evaluate the validity of the cognate set.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 2364


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | The title of a table of related forms; typically hints at the type of relation between the forms or between the group of forms and an etymon.
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
`Category` | `string` | An optional category for groups of forms such as "loans".
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Cognateset_ID](http://cldf.clld.org/v1.0/terms.rdf#cognatesetReference) | `string` | Links to an etymon, if the group of lexemes is related to one.<br>References [cognatesets.csv::ID](#table-cognatesetscsv)
`Dempwolff_Etymology` | `string` | A corresponding (unsupported) reconstruction posited in Dempwolff 1938.

## <a name="table-cfitemscsv"></a>Table [cfitems.csv](./cfitems.csv)

Membership of forms in a "cf" group is mediated through this association table unless more meaningful alternatives are available, like BorrowingTable for loans.

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 7344


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
`Cfset_ID` | `string` | References [cf.csv::ID](#table-cfcsv)
[Form_ID](http://cldf.clld.org/v1.0/terms.rdf#formReference) | `string` | References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-borrowingscsv"></a>Table [borrowings.csv](./borrowings.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF BorrowingTable](http://cldf.clld.org/v1.0/terms.rdf#BorrowingTable)
[dc:extent](http://purl.org/dc/terms/extent) | 7348


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Target_Form_ID](http://cldf.clld.org/v1.0/terms.rdf#targetFormReference) | `string` | References the loanword, i.e. the form as borrowed into the target language<br>References [forms.csv::ID](#table-formscsv)
[Source_Form_ID](http://cldf.clld.org/v1.0/terms.rdf#sourceFormReference) | `string` | References the source word of a borrowing<br>References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Cfset_ID` | `string` | Link to a set description.<br>References [cf.csv::ID](#table-cfcsv)

## <a name="table-etymacsv"></a>Table [etyma.csv](./etyma.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 8161


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | A numeric identifier for the etymon. For etyma present in the legacy online version of ACD this number will match the cognate set number assigned then.<br>Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | The core reconstruction uniting the cognate sets of the etymon.
`Initial` | `string`<br>Valid choices:<br> `a` `b` `c` `C` `d` `e` `g` `h` `i` `j` `k` `l` `m` `n` `N` `ñ` `ŋ` `o` `p` `q` `r` `R` `s` `S` `t` `u` `w` `y` `z` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | The reconstructed meaning of the etymon.
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | Some notes are several lines, while others are a page or more. Notes are used for a variety of purposes. Among the most common are to report other forms that show a likely historical connection with those cited in the main comparison, but which exhibit irregularities other than the usual sporadic assimilation or metathesis, and so raise more serious questions about comparability, as in entry (2) above; to discuss details of the reconstructed gloss; and to note the occurrence of monosyllabic “roots” or submorphemic sound-meaning correlations in reconstructed morphemes.
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | Sources mentioned in the comment describing the etymon.<br>References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-treescsv"></a>Table [trees.csv](./trees.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF TreeTable](http://cldf.clld.org/v1.0/terms.rdf#TreeTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | Name of tree as used in the tree file, i.e. the tree label in a Nexus file or the 1-based index of the tree in a newick file
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | Describe the method that was used to create the tree, etc.
[Tree_Is_Rooted](http://cldf.clld.org/v1.0/terms.rdf#treeIsRooted) | `boolean`<br>Valid choices:<br> `Yes` `No` | Whether the tree is rooted (Yes) or unrooted (No) (or no info is available (null))
[Tree_Type](http://cldf.clld.org/v1.0/terms.rdf#treeType) | `string`<br>Valid choices:<br> `summary` `sample` | Whether the tree is a summary (or consensus) tree, i.e. can be analysed in isolation, or whether it is a sample, resulting from a method that creates multiple trees
[Tree_Branch_Length_Unit](http://cldf.clld.org/v1.0/terms.rdf#treeBranchLengthUnit) | `string`<br>Valid choices:<br> `change` `substitutions` `years` `centuries` `millennia` | The unit used to measure evolutionary time in phylogenetic trees.
[Media_ID](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | References a file containing a Newick representation of the tree, labeled with identifiers as described in the LanguageTable (the [Media_Type](https://cldf.clld.org/v1.0/terms.html#mediaType) column of this table should provide enough information to chose the appropriate tool to read the newick)<br>References [media.csv::ID](#table-mediacsv)
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string`<br>Regex: `[^/]+/.+` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
[Path_In_Zip](http://cldf.clld.org/v1.0/terms.rdf#pathInZip) | `string` | 

