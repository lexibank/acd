import pathlib

from acdparser import parse


if __name__ == '__main__':
    parse(pathlib.Path('raw'))
