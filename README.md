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

## Regenerating productions.bnf

At https://yaml.org/spec/1.2.1/ run in dev console:

```javascript
copy([...new Set([...document.getElementsByClassName("productionset")]
    .map(x => x.innerText))]
  .join('\n')
  .replace(/\s*\[\d+\]\s*/g, '\n\n')
  .replace(/\\/g, '\\\\')
  .replace(/"/g, '\\"')
  .replace(/[“”]/g, '"')
  .replace(/\xA0/g, ' ')
  .replace(/\t/g, ' ')
  .replace(/(\S+) ::= ([^\n]+(?:\n[^\n]+)*)/g, (m, n, d) => 
    `${n} ::= ${d.replace(/\n/g, '\n' + ' '.repeat(5 + n.length))}`))
```
