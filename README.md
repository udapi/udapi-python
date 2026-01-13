# udapi-python
Python framework for processing Universal Dependencies data

[![Build Status](https://circleci.com/gh/udapi/udapi-python.svg?style=shield)](https://circleci.com/gh/udapi/udapi-python)
[![Website](https://img.shields.io/website-up-down-green-red/http/udapi.github.io.svg)](http://udapi.github.io)
[![Documentation Status](https://readthedocs.org/projects/udapi/badge/)](http://udapi.readthedocs.io)

## Requirements
- You need Python 3.9 or higher.
- It is recommended to install Udapi in a Python virtual environment.
- If you need the [ufal.udpipe](https://pypi.python.org/pypi/ufal.udpipe/) parser (to be used from Udapi)
  install it (with `pip install --upgrade ufal.udpipe`).

## Install Udapi for developers
Let's clone the git repo e.g. to `~/udapi-python/` and make an [editable installation](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)
```bash
cd
git clone https://github.com/udapi/udapi-python.git
cd udapi-python
pip install -e .
```

## Install Udapi for users
This is similar to the above, but installs Udapi from PyPI to the standard (user) Python paths.
```
pip install --upgrade udapi
```
Try `udapy -h` to check it is installed correctly.
If it fails, make sure your `PATH` includes the directory where `pip3` installed the `udapy` script.
Usually, this results in
```bash
export PATH="$HOME/.local/bin/:$PATH"
```
