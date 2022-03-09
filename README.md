# Pyrrowhead - The CLI local cloud management tool!

[![CI](https://github.com/ajoino/pyrrowhead/actions/workflows/ci.yml/badge.svg)](https://github.com/ajoino/pyrrowhead/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ajoino/pyrrowhead/branch/main/graph/badge.svg?token=E9OR4SEIKS)](https://codecov.io/gh/ajoino/pyrrowhead)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![pypi](https://img.shields.io/pypi/v/pyrrowhead)](https://pypi.org/project/pyrrowhead/)
[![python](https://img.shields.io/pypi/pyversions/pyrrowhead)](https://pypi.org/project/pyrrowhead/)
[![readthedocs](https://img.shields.io/readthedocs/pyrrowhead)](https://pyrrowhead.readthedocs.io/en/latest/)

Pyrrowhead is a command line tool for creating and managing Arrowhead local clouds.


Install it with `pip install pyrrowhead` and create your first local cloud as simple as
```bash
pyrrowhead cloud create hello-cloud.world
```
This will create a cloud called `hello-cloud` under an organization called world.

Pyrrowhead utilizes the Arrowhead docker containers to run local clouds, for example:
```bash
pyrrowhead cloud up hello-cloud.world
```

Check out the [tutorial](https://pyrrowhead.readthedocs.io/en/latest/tutorial.html) for more information.
