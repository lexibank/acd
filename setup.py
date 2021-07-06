from setuptools import setup, find_packages
import json


with open('metadata.json', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name="lexibank_acd",
    description=metadata["title"],
    license=metadata.get("license", ""),
    url=metadata.get("url", ""),
    py_modules=["lexibank_acd"],
    packages=find_packages(where='.'),
    include_package_data=True,
    zip_safe=False,
    entry_points={"lexibank.dataset": ["gaotb=lexibank_gaotb:Dataset"]},
    install_requires=[
        'lxml',
        'bs4',
        'nameparser',
    ],
    extras_require={"test": ["pytest-cldf"]},
)
