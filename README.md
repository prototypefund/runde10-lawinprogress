<br />
<div align="center">
  <a href="https://gitlab.com/nototast/lawinprogress/">
    <img src="resources/law-in-progress-logo.png" alt="Law in Progress" height="80">
  </a>

  <p align="center">
    <br />
    Das Online-Tool "Law in Progress" macht Gesetzentwürfe und deren Konsequenzen für bestehende Gesetze durch automatische Erstellung einer Synopse sichtbar und nachvollziehbar.
    Aktuell werden nur Entwürfe von Bundesgesetzen unterstützt. Später sollen auch Entwürfe von Landesgesetzen genutzt werden können.
    <br />
    <br />
    <a href="https://www.app.lawinprogress.de">View Demo</a>
    ·
    <a href="">Report Bug</a>
    ·
    <a href="mailto: hello@lawinprogress.de">Request Feature</a>
    <br />
    <br />
    <img src="resources/law_in_progress_how_to.gif" alt="Law in Progress - How to">
  </p>
</div>

## Installation

Clone the repo and run `make poetry` and `make install` to setup poetry and the relevant requriements.


## Web-App

Run `make app` to start the webapp at `localhost:8000`.

## Overview

```
├── pyproject.toml       --> Config for the project
├── README.md            --> This file
├── LICENSE              --> MIT license 
├── Makefile             --> Make target for setup, testing and cleaning
├── logging.conf         --> Configuration for the loggers used in this project
├── data/                --> Folder with some raw files of laws in text and pdf
├── doc/                 --> Documentation and notes
├── notebooks/           --> Experimental notebooks
├── lawinprogress/       --> Main package
│   ├── __init__.py
│   ├── generate_diff.py --> main script to generate a diff from a change law
│   ├── parsing/         --> modules to parse source and change laws
│   ├── apply_changes/   --> modules to apply the proposed changes to source laws
│   ├── app/             --> contains the FastAPI webapp.
│   └── libdiff/         --> modules to generate a html diff of the changed law
└── tests/               --> Test for the main package
    ├── ...
    └── __init__.py
```


## Example usage as a script
To generate a diff for an exisiting change law, run

```bash
poetry run python ./lawinprogress/generate_diff.py -c data/0483-21.pdf --html
```

This will generate a before and after version of the changed laws, as well as a html file highlighting the diffs in `./output`.
Currently only changes in laws present in `./data/source_laws/` are supported. Other changes will be skipped.

## Code checks & tests

You can run the code checks (with isort, black and pylint) by running `make check`.
This will first sort the imports with `isort` and then format the code with `black`.
These tools might not agree on something, but in the end the code looks nice.
Finally, some properties of code "quality" are checked with `pylint`.
Try to resolve as many warnings as reasonably possible. If you are sure you want to ignore a warning,
you can comment the line (or in the line before the warning) in the source code ```# pylint: disable=<name-of-the-warning>```.

To run the tests, run `make test`.

## Acknowledgements

* Funded from September 2021 until February 2022 by ![logos of the "Bundesministerium für Bildung und Forschung", Prodotype Fund and OKFN-Deutschland](resources/pf_funding_logos.svg)
