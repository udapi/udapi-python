# udapi-python
Python framework for processing Universal Dependencies data

[![Build Status](https://travis-ci.org/udapi/udapi-python.svg?branch=master)](https://travis-ci.org/udapi/udapi-python)

## Requirements
- You need Python 3.3 or higher.

## Install Udapi for developers
Let's clone the git repo to `~/udapi-python/`, install dependencies
and setup `$PATH` and `$PYTHONPATH` accordingly.
```bash
cd
git clone https://github.com/udapi/udapi-python.git
pip3 install --user -r udapi-python/requirements.txt
echo '## Use Udapi from ~/udapi-python/ ##'                >> ~/.bashrc
echo 'export PATH="$HOME/udapi-python/bin:$PATH"'          >> ~/.bashrc
echo 'export PYTHONPATH="$HOME/udapi-python/:$PYTHONPATH"' >> ~/.bashrc
source ~/.bashrc # or open new bash
```

## Install Udapi for users
This is similar to the above, but installs Udapi to the standard (user) Python paths.
```
pip3 install --user --upgrade git+https://github.com/udapi/udapi-python.git
```
