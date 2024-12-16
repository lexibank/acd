"""
Validation of the data in this dataset
"""
# FIXME:
# - etym with cfset: 27604
# - loanset
# - root
# - noise with Dempwolff etym
# - near
# - metathesis + assimilation 27617
#
# *Cakaw steal : table in description!
#
# Example: Malagasy dzuluka,
#listed for two Noise sets
#
#Incomplete word form referenced in Noise set "pierce, skewer" and "skewer:   pierce, skewer"
#https://www.trussel2.com/ACD/acd-n_p.htm
#https://www.trussel2.com/ACD/acd-n_s.htm
#
#dzuluka (<l?)< td=""></l?)<>

import shlex
import itertools
import contextlib
import subprocess
import collections

import matplotlib.pyplot as plt

from lexibank_acd import Dataset

ECOUNT_DIFFS = {
    'a': 20,  # +5 2021-08-01.odt, +15 2021-09-13.odt
    'g': 1,  # +1 2021-09-13.odt
    'l': 1,  # +1 2021-08-01.odt
}
FCOUNT_DIFFS_V1_1 = {  # Added forms per language between v1.0 and v1.1:
    "19083": 20, "279": 9, "825": 8, "19012": 6, "423": 6, "18976": 5, "252": 5, "819": 4,
    "273": 3, "920": 3, "19182": 3, "675": 2, "331": 2, "244": 2, "226": 2, "636": 2, "19081": 1,
    "391": 1, "1060": 1, "19189": 1, "19175": 1, "19275": 1, "19486": 1, "289": 1, "18225": 1,
    "18831": 1, "569": 1, "19094": 1, "291": 1, "276": 1, "427": 1}


@contextlib.contextmanager
def plot(fname, title, xlabel, ylabel):
    fig, ax = plt.subplots()
    fig.set_figheight(8)
    fig.set_figwidth(10)
    try:
        yield ax
    finally:
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.set_title(title)
        #ax.grid(True)
        fig.tight_layout()
        plt.savefig(str(fname))
        plt.show()


def run_cmd(cmd):
    return subprocess.check_output(
        shlex.split(cmd) if isinstance(cmd, str) else cmd).decode("utf-8")


def run(args):
    sql_aNak_1 = """select
    count(distinct l.cldf_id) as nlangs 
from 
    languagetable as l
  join formtable as f on f.cldf_languagereference = l.cldf_id 
  join cognatetable as c on f.cldf_id = c.cldf_formreference 
  join cognatesettable as cs on c.cldf_cognatesetreference = cs.cldf_id
  join `etyma.csv` as e on cs.etymon_id = e.cldf_id
where 
    l.is_proto = false and cs.is_main_entry = true and e.cldf_name = '*aNak';"""

    cmd_ex1 = 'cldfbench acd.etymon qeCeŋ --with-reconstruction-tree'
    cmd_ex2 = 'cldfbench acd.etymon kudis'
    cmd_ex3 = 'cldfbench acd.etymon handem'
    cmd_ex4 = 'cldfbench acd.etymon qaCi'


    ds = Dataset()
    cldf = ds.cldf_reader()
    lcounts = {r['ID']: r for r in ds.etc_dir.read_csv('lcounts.tsv', delimiter='\t', dicts=True)}
    #
    # We have identified words when they had same form and meaning description, and split forms
    # in case multiple forms were listed in one entry, split by ","
    #
    diffs = collections.defaultdict(list)
    for lid, forms in itertools.groupby(
            sorted(cldf['FormTable'], key=lambda f: f['Language_ID']), lambda f: f['Language_ID']):
        count = sum(1 for _ in forms)
        if lid in FCOUNT_DIFFS_V1_1:
            count - FCOUNT_DIFFS_V1_1[lid]

        if lid not in lcounts:
            assert int(lid) > 20000
        else:
            orig = lcounts[lid]
            if not orig['Name'].startswith('Proto'):
                diffs[count - int(orig['Count'])].append(orig['Name'])

    x, y = [], []
    for k, v in sorted(diffs.items()):
        x.append(k)
        y.append(len(v))

    with plot('etc/lcount.png',
              'Differences in word counts per language',
              'Difference in words',
              'Number of languages') as ax:
        #fig, ax = plt.subplots(figsize=(14, 10), dpi=80)
        ax.bar(x, y, edgecolor='black', linewidth=1, color='orange')
        ax.set_yscale('log')

    #
    # second graph
    #
    old = collections.OrderedDict(
        (r['grapheme'], int(r['count'])) for r in ds.etc_dir.read_csv('counts.csv', dicts=True))
    new = collections.Counter(etymon['Initial'] for etymon in cldf['etyma.csv'])
    nums = []
    for grapheme, count in old.items():
        if count + ECOUNT_DIFFS.get(grapheme, 0) != new[grapheme]:
            nums.append((grapheme, new[grapheme] - count))

    #plt.figure(figsize=(14, 10), dpi=80)
    with plot('etc/ecount.png',
              'Difference in number of etyma per grapheme',
              'Difference in number of etyma',
              'First grapheme of reconstruction') as ax:
        # Plotting the horizontal lines
        plt.hlines(
            y=[i for i, _ in enumerate(nums, start=1)],
            xmin=[min([n, 0]) for _, n in nums],
            xmax=[max([n, 0]) for _, n in nums],
            color=['red' if n < 0 else 'blue' for _, n in nums], alpha=0.4, linewidth=30)
        # Decorations
        # Setting Date to y-axis
        plt.yticks([i for i, _ in enumerate(nums, start=1)], [n[0] for n in nums], fontsize=12)
        plt.xticks([-1, 1])

        # Optional grid layout
        plt.grid(linestyle='--', alpha=0.5)

    ecount_cmd = [
        'sqlite3',
        'acd.sqlite',
        'select initial, count(cldf_id) from "etyma.csv" group by initial order by lower(initial)',
        '-separator', ','
    ]
    ps = subprocess.Popen(ecount_cmd, stdout=subprocess.PIPE)
    ecount_res = subprocess.check_output(['termgraph'], stdin=ps.stdout).decode("utf-8")
    ps.wait()

    md = """# Validating the ACD dataset'

## Completeness

By far the mojority of the data in this dataset was extracted from the legacy online version at https://trussel2.com/ACD/ .
To assess the completeness of this extraction, two sets of numbers are available for comparison.


### The number of cognate sets per initial grapheme

The legacy HTML pages list the numbers of cognate sets as follows:

![](etc/graph-letcount.gif)

Recomputing such numbers for the current dataset is simple. Running
```
$ {} | grep termgraph
```
we get
```
{}
```

If we recompute these numbers for the current dataset and adjust them according to the 22 sets added between
v1.0 and v.1.2, we get the following minimal differences for six initials:

![](etc/ecount.png)


### The number of word forms per language 

These numbers are listed on the pages under [Languages](https://trussel2.com/ACD/acd-l_a.htm).
When extracting the data we have identified words when they had same form and meaning description, 
and split forms in cases when multiple forms were listed in one entry, split by ",". Thus, differences
in both directions between the old and the current numbers are expected to some degree. Still, for the
majority of languages we get (near) identical numbers:

![](etc/lcount.png)


## Correctness

To validate our CLDF dataset, we recreate the examples cited in 'The Austronesian Comparative Dictionary: A Work in Progress'
(published as Research Note in Oceanic Linguistics in 2013)
thereby illustrating that our extraction of the legacy data fromt the HTML pages at https://trussel2.com/ACD/ was accurate.
It should be noted that the research note describes the status of the ACD as of 2013, with a "current total" of 4,837 cognate
sets, whereas in 2020 -- the state represented at https://trussel2.com/ACD/ -- it contained more than 8,000 sets. Thus, a lot
of work went into the dictionary after 2013, but we should expect the majority of this work being additions rather than removal
or correction of content.

Recreation of cognate sets in the visual form presented in the research note (which served also as a template for the
HTML representation at https://trussel2.com/ACD/) is done via a `cldfbench` subcommand [`acd.etymon`](acdcommands/etymon.py),
distributed with our dataset.


## Example 1:

![](etc/ol-ex1.png)

Running
```shell
{}
```
we get
```
{}
```
> [!NOTE]
> Our dataset also contains the topology of the assumed sub-group tree underlying the reconstructions. Thus,
> we can plot the reconstruction at each level on this tree, providing a visualization of the postulated
> sound changes.


## Example 2:

![](etc/ol-ex2.png)

Running
```shell
{}
```
we get
```
{}
```

> [!NOTE]
> Due that due to inclusion of Formosan evidence (between 2013 and 2020), *kudis is now reconstructed to PAN.


## Example 3:

![](etc/ol-ex3.png)

Running
```shell
{}
```
we get
```
{}
```

> [!NOTE]
> At some point after 2013 an explicit Philippine subgroup has been added to the ACD.


## Example 4:

![](etc/ol-ex4.png)

Running
```shell
{}
```
we get
```
{}
```


## Miscellaneous

The research note contains several other statements about the contents of the dataset, which we can verify.
We use this verification to also illustrate how to efficiently access the relational data. Since each CLDF
dataset can easily be converted to a SQLite database, we use the SQLite representation and the SQL query
language in the following.

The paper states that

> it should be noted that PAN *aNak ‘child’, which is 15 single-spaced
> pages in print form, is supported by reflexes in 101 languages, and the main entry is fol-
> lowed by 46 subentries, which include prefixed, suffixed, and circumfixed forms of the
> base, prefixed and suffixed forms of the base, partial and full reduplications, and a num-
> ber of compounds, such as PMP *anak apij ‘twin’, PMP *anak bahi/ba-bahi/b<in>ahi
> ‘wife-taking group’, PMP *anak buaq ‘relative’, PWMP *anak daRa ‘virgin, girl of mar-
> riageable age’, PMP *anak ma-Ruqanay/(la)-laki ‘wife-giving group’, PWMP *anak
> haRezan ‘step or rung of a ladder’, PMP *anak i mata ‘pupil of the eye’, and *anak i
> panaq ‘arrow’.

Counting distinct languages of reflexes for a set can be done with the following query:
```sql
{}
```
resulting in
```
{}
```
Counting the subsets for an etymon is very simple:
```sql
sqlite> select count(*) from cognatesettable as cs, `etyma.csv` as e where cs.etymon_id = e.cldf_id and e.cldf_name = '*aNak';
48 
```

Testing whether a particular reconstruction is listed for a subset can be done as
```sql
sqlite> select exists(select cs.cldf_name from cognatesettable as cs, `etyma.csv` as e where cs.etymon_id = e.cldf_id and e.cldf_name = '*aNak' and cs.cldf_name like '%*anak apij%');
1
```

""".format(
        ' '.join(["'" + arg + "'" if ' ' in arg else arg for arg in ecount_cmd]),
        ecount_res.strip(),
        cmd_ex1,
        run_cmd(cmd_ex1),
        cmd_ex2,
        run_cmd(cmd_ex2),
        cmd_ex3,
        run_cmd(cmd_ex3),
        cmd_ex4,
        run_cmd(cmd_ex4),
        sql_aNak_1,
        run_cmd(['sqlite3', 'acd.sqlite', '-header', sql_aNak_1]),
    )
    ds.dir.joinpath('VALIDATION.md').write_text(md, encoding='utf-8')
