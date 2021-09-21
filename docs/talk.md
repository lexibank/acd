# ACD fact sheet

The Austronesian Comparative Dictionary

Status quo ante: https://www.trussel2.com/acd/ (For even earlier states, refer to https://www.trussel2.com/acd/ACD-OL.pdf)
Status quo post: https://acd.clld.org/

Transition implemented via cldfbench curated CLDF dataset at
https://github.com/lexibank/acd


## Overview

- it's big:
  ```
  $ cldf stats cldf/cldf-metadata.json
  ...
                     Type                 Rows
  -----------------  -----------------  ------
  forms.csv          FormTable          146642
  languages.csv      LanguageTable        1062
  parameters.csv     ParameterTable      86494
  cognates.csv       CognateTable       116662
  contributions.csv  ContributionTable       5
  cognatesets.csv    CognatesetTable      9377
  loansets.csv                             998
  borrowings.csv     BorrowingTable       7348
  protoforms.csv                         24884
  ```

- it's the product of one brain - so possibly more consistent than average(?)
  (at least when it comes to transcriptions?)
  -> but then - who's got the same brain for 51 years?

One of those etymological dictionaries that morphed from qualitative work
to a size where only quantitative analysis seems appropriate ...


## Opportunities

- reconstructions on multiple levels - perfect material to investigate
  semantic shift? https://acd.clld.org/cognatesets/27605

- there may be more of the same to come (Gerwen's Nubian etym dict) also the
  Comparative Siouan Dictionary https://csd.clld.org/parameters/1146

- Merge with ABVD?
  ```
                  Type              Rows
  --------------  --------------  ------
  forms.csv       FormTable       313273
  languages.csv   LanguageTable     1632
  parameters.csv  ParameterTable     210
  cognates.csv    CognateTable    233260
  sources.bib     Sources            824
  ```
  Overlap in terms of doculects with ABVD:
  ```sql
  $ sqlite3
  sqlite> attach database `acd.sqlite` as acd;
  sqlite> attach database `../../abvd/abvd-cldf/abvd.sqlite` as abvd;
  sqlite> select count(distinct cldf_glottocode) from acd.languagetable;
  795

  sqlite> select count(distinct cldf_glottocode) from acd.languagetable where cldf_glottocode is not null and cldf_glottocode in (select cldf_glottocode from abvd.languagetable);
  550
  ```
  Overlap in terms of concepts:
  would require linking to concepticon - maybe semi-automatically, based on form/language pairs?


## Challenges

- very variable coverage
  - coverage of languages/varieties
    ```
    $ sqlite3 acd.sqlite "select cast(c * 100 + 100 as int), count(lid) from (select cldf_languagereference as lid, round(count(cldf_id) / 100, 0) as c from formtable group by cldf_languagereference) group by c" | termgraph --delim "|"

    100 : ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 864.00
    200 : ▇▇▇ 65.00
    300 : ▇ 27.00
    400 : ▇ 24.00
    500 : ▏ 14.00
    600 : ▏ 11.00
    700 : ▏ 4.00
    800 : ▏ 8.00
    900 : ▏ 6.00
    1000: ▏ 8.00
    1100: ▏ 5.00
    1200: ▏ 5.00
    1300: ▏ 2.00
    1500: ▏ 1.00
    1600: ▏ 1.00
    1700: ▏ 2.00
    1800: ▏ 1.00
    1900: ▏ 1.00
    2000: ▏ 2.00
    2100: ▏ 2.00
    2200: ▏ 1.00
    2300: ▏ 1.00
    2700: ▏ 1.00
    2900: ▏ 1.00
    3000: ▏ 1.00
    3100: ▏ 1.00
    3700: ▏ 1.00
    4000: ▏ 1.00
    4200: ▏ 2.00
    7900: ▏ 1.00
    ```
    
 - individual cognate sets:
   - https://acd.clld.org/cognatesets/30830 - 1031 witnesses grouped in almost 40 associated reconstructions
   - https://acd.clld.org/cognatesets/24748 - 2 witnesses
   - https://acd.clld.org/cognatesets/30164
     > As noted in Blust (1982b) from a morphological standpoint this is one of the most challenging of all Austronesian comparisons. In addition to the reduplicated and infixed forms of *bahi that are reconstructed here there are numerous other affixed forms that are confined to particular languages or genetically restricted groups of languages, and a few that are widespread but semantically heterogeneous.
    - https://acd.clld.org/cognatesets/25870 with a ~10,000 character comment ...

- non-normalized glosses:
  ```
  $ csvstat -c Name cldf/parameters.csv
    2. "Name"

  >-------Type of data:          Text
  >-------Contains null values:  True (excluded from calculations)
  >-------Unique values:         86494
  >-------Longest value:         2.532 characters
  >-------Most common values:    bad (1x)
  >-------                       lime (for betel) (1x)
  >-------                       fire (1x)
  >-------                       knee (1x)
  >-------                       ember, glowing coal (1x)
  ```
- non-trivial update process


## Conclusion

"Panta Rei" - and now is the time to influence the future by formulating
research questions making use of ACD!
