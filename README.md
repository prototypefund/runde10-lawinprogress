# Law in Progress

Das Online-Tool "Law in Progress" soll Gesetzentwürfe und deren Konsequenzen für bestehende Gesetze durch automatische Erstellung einer Synopse sichtbar und nachvollziehbar zu machen.


# Overview

```
├── pyproject.toml      --> Config for the project
├── README.md           --> 
├── LICENSE             --> MIT license 
├── Makefile            --> Make target for setup, testing and cleaning
├── data/               --> Folder with some data
├── doc/                --> Documentation and notes
├── notebooks/          --> Experimental notebooks
├── lawinprogress/      --> Main package
│   ├── __init__.py
│   └── generate_diff.py --> main script to generate a diff from a change law
└── tests/              --> Test for the main package
    └── __init__.py
```

# Setup

Clone the repo and run `make install` to setup poetry and the relevant requriements.

# Example usage:

```poetry run python ./lawinprogress/generate_diff.py -c data/0483-21.pdf```


# Code checks & tests

You can run the code checks (with isort, black and pylint) by running `make check`.
This will first sort the imports with `isort` and then format the code with `black`.
These tools might not agree on something, but in the end the code looks nice.
Finally, some properties of code "quality" are checked with `pylint`.
Try to resolve as many warnings as reasonably possible. If you are sure you want to ignore a warning,
you can comment the line (or in the line before the warning) in the source code
```
# pylint: disable=<name-of-the-warning>
```

To run the tests, run `make test`.
