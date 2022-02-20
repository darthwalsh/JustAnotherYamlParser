# Just Another YAML Parser

Clone like `git clone --recurse-submodules ...`

## Running tests

Set up a virtual environment:

    python3 -m venv env

On macOS and Linux:

    source env/bin/activate

Or on Windows:

    .\env\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Run tets:

    pytest

## Roadmap

- [ ] Debug parsing showing how each rule is applied
- [ ] Parsing *presentation* (text) into *serialization* tree
- [ ] Composing *serialization* into *representation* JSON

## Regenerating 1.2.2 productions.bnf

https://yaml.org/spec/1.2.2/ contains HTML for the spec, but [yaml/yaml-spec](https://github.com/yaml/yaml-spec.git) has the markdown source.

Run script `produce_bnf.py` which uses yaml-spec as a submodule to produce `productions.bnf`.

At https://yaml.org/spec/1.2.2/ run in dev console:
