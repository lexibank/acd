# Using the ACD CLDF data

## Overview

The ACD data is formatted as [cognate-coded CLDF Wordlist](cldf/README.md).
Thus, the [cognate sets](https://acd.clld.org/cognatesets), as familiar from the ACD website, can
be accessed by aggregating data from the
- *CognatesetTable* - reconstructed proto-form and meaning from the *Form* and *Description* columns and a link to the proto-language,
- *CognateTable* - the association table linking forms to cognatesets,
- *FormTable* - the related word forms and links to their language and meaning,
- *ParameterTable* - the word meanings, and
- *LanguageTable*.

![](etc/erd.svg)

Aggregating data across five tables can be somewhat cumbersome, though, without the support of a suitable
computing environment. Thus, we recommend to access the data either using `pycldf` (see below) - if working
in Python - or via a SQLite database created from the CLDF data.


## Using `pycldf`

FIXME `pycldf.orm` example.


## Using SQLite

FIXME
