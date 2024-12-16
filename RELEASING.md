# Releasing the ACD

```shell
cldfbench lexibank.makecldf lexibank_acd.py --glottolog-version v5.1 --dev
```

```shell
cldf validate cldf --with-cldf-markdown
```

```shell
rm -f acd.sqlite
cldf createdb cldf acd.sqlite
```

```shell
cldfbench acd.validation
```

```shell
cldfbench cldfreadme lexibank_acd.py
cldfbench zenodo lexibank_acd.py
```

```shell
cldferd cldf --db acd.sqlite --format compact.svg --output etc/erd.svg
```

```shell
cldfbench cldfviz.map cldf/ --language-properties Group --format png --pacific-centered --output etc/map.png --height 10 --width 30 --with-ocean --projection Mollweide --padding-left 2 --padding-top 1 --padding-bottom 3 --padding-right 1 --markersize 5
```
