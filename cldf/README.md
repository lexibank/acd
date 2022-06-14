<a name="ds-cldfmetadatajson"> </a>

# Wordlist CLDF dataset derived from Blust's "Austronesian Comparative Dictionary"

**CLDF Metadata**: [cldf-metadata.json](./cldf-metadata.json)

**Sources**: [sources.bib](./sources.bib)

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | The Austronesian Comparative Dictionary
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Wordlist](http://cldf.clld.org/v1.0/terms.rdf#Wordlist)
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by/4.0/
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/lexibank/acd
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/lexibank/acd/tree/d307fb6">lexibank/acd v1.1-6-gd307fb6</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v4.6">Glottolog v4.6</a></li><li><a href="https://github.com/concepticon/concepticon-data/tree/v2.6.0">Concepticon v2.6.0</a></li><li><a href="https://github.com/cldf-clts/clts/tree/2c6e122">CLTS v2.1.0-33-g2c6e122</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>lingpy-rcParams</strong>: <a href="./lingpy-rcParams.json">lingpy-rcParams.json</a></li><li><strong>python</strong>: 3.8.10</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | acd
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-formscsv"></a>Table [forms.csv](./forms.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF FormTable](http://cldf.clld.org/v1.0/terms.rdf#FormTable)
[dc:extent](http://purl.org/dc/terms/extent) | 146642


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
`is_root` | `boolean` | 
`is_proto` | `boolean` | 

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1062


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string` | 
`Glottolog_Name` | `string` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal` | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal` | 
`Family` | `string` | 
`ISOname` | `string` | 
`Group` | `string` | 
`Location` | `string` | 
`Alias` | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`is_proto` | `boolean` | 
`Dialect_Of` | `string` | 

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 86494


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
[dc:extent](http://purl.org/dc/terms/extent) | 116662


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
`Proto_Language` | `string` | 
`Reconstruction_ID` | `string` | References [protoforms.csv::ID](#table-protoformscsv)

## <a name="table-contributionscsv"></a>Table [contributions.csv](./contributions.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ContributionTable](http://cldf.clld.org/v1.0/terms.rdf#ContributionTable)
[dc:extent](http://purl.org/dc/terms/extent) | 5


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Contributor](http://cldf.clld.org/v1.0/terms.rdf#contributor) | `string` | 
[Citation](http://cldf.clld.org/v1.0/terms.rdf#citation) | `string` | 

## <a name="table-cognatesetscsv"></a>Table [cognatesets.csv](./cognatesets.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CognatesetTable](http://cldf.clld.org/v1.0/terms.rdf#CognatesetTable)
[dc:extent](http://purl.org/dc/terms/extent) | 9377


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Form` | `string` | 
`Comment` | `string` | 
`Proto_Language` | `string` | 
`Contribution_ID` | `string` | References [contributions.csv::ID](#table-contributionscsv)

## <a name="table-loansetscsv"></a>Table [loansets.csv](./loansets.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 998


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
`ID` | `string` | Primary key
`Gloss` | `string` | 
`Dempwolff_Etymology` | `string` | 
`Contribution_ID` | `string` | References [contributions.csv::ID](#table-contributionscsv)
`Comment` | `string` | 

## <a name="table-borrowingscsv"></a>Table [borrowings.csv](./borrowings.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF BorrowingTable](http://cldf.clld.org/v1.0/terms.rdf#BorrowingTable)
[dc:extent](http://purl.org/dc/terms/extent) | 7348


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Target_Form_ID](http://cldf.clld.org/v1.0/terms.rdf#targetFormReference) | `string` | References the loanword, i.e. the form as borrowed into the target language<br>References [forms.csv::ID](#table-formscsv)
[Source_Form_ID](http://cldf.clld.org/v1.0/terms.rdf#sourceFormReference) | `string` | References the source word of a borrowing<br>References [forms.csv::ID](#table-formscsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Loanset_ID` | `string` | References [loansets.csv::ID](#table-loansetscsv)

## <a name="table-protoformscsv"></a>Table [protoforms.csv](./protoforms.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 24884


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
`ID` | `string` | Primary key
`Cognateset_ID` | `string` | References [cognatesets.csv::ID](#table-cognatesetscsv)
`Form_ID` | `string` | References [forms.csv::ID](#table-formscsv)
`Subset` | `string` | 
`Proto_Language` | `string` | 
`Comment` | `string` | 
`Inferred` | `boolean` | 
`Doublet_Comment` | `string` | 
`Disjunct_Comment` | `string` | 
`Doublets` | list of `string` (separated by ` `) | variants that are independently supported by the comparative evidence<br>References [protoforms.csv::ID](#table-protoformscsv)
`Disjuncts` | list of `string` (separated by ` `) | References [protoforms.csv::ID](#table-protoformscsv)

