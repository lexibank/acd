from setuptools import setup
import json


with open('metadata.json', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_acd',
    description=metadata['title'],
    license=metadata.get('license', ''),
    url=metadata.get('url', ''),
    py_modules=['lexibank_acd'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.commands': [
            'acd=acdcommands',
        ],
        'lexibank.dataset': [
            'acd=lexibank_acd:Dataset',
        ]
    },
    install_requires=[
        'cldfviz>=0.7',
        'clldutils>=3.11',
        'pylexibank>=3.2.0',
        'lxml',
        'bs4',
        'nameparser',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
