# udapi-python
Python framework for processing Universal Dependencies data

[![Build Status](https://circleci.com/gh/udapi/udapi-python.svg?style=shield)](https://circleci.com/gh/udapi/udapi-python)
[![Website](https://img.shields.io/website-up-down-green-red/http/udapi.github.io.svg)](http://udapi.github.io)
[![Documentation Status](https://readthedocs.org/projects/udapi/badge/)](http://udapi.readthedocs.io)

## Requirements
- You need Python 3.6 or higher.
- If the [ufal.udpipe](https://pypi.python.org/pypi/ufal.udpipe/) parser is needed,
  make sure you have a C++11 compiler (e.g. [g++ 4.7 or newer](.travis.yml#L9))
  and install UDPipe with `pip3 install --user --upgrade ufal.udpipe`.

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
This is similar to the above, but installs Udapi from PyPI to the standard (user) Python paths.
```
pip3 install --user --upgrade udapi
```
Try `udapy -h` to check it is installed correctly.
If it fails, make sure your `PATH` includes the directory where `pip3` installed the `udapy` script.
Usually, this results in
```bash
export PATH="$HOME/.local/bin/:$PATH"
```
