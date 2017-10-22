#!/bin/bash

if ! which virtualenv >/dev/null; then
    echo virtualenv is not installed.
    echo please run pip3 install virtualenv.
    exit 0
fi

if [ -d dev_venv ]; then
    echo installing virtualenv...
    pip3 install virtualenv
fi

virtualenv venv

source venv/bin/activate

# update pip to the latest version
python3 -m pip install -U pip

pip3 install -e .
