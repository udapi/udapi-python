"""Utilities for downloading models and ither resources."""
import logging
import urllib.request
import os

BASEURL = 'http://ufallab.ms.mff.cuni.cz/tectomt/share/data/'

def require_file(path):
    """Return absolute path to the file and download it if missing."""
    if path.startswith('/') or path.startswith('.'):
        if not os.path.isfile(path):
            raise IOError(path + " does not exist")
        return os.path.abspath(path)
    udapi_data = os.environ.get('UDAPI_DATA', os.environ.get('HOME'))
    full_path = udapi_data + '/' + path
    if not os.path.isfile(full_path):
        logging.info('Downloading %s to %s', BASEURL + path, full_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        urllib.request.urlretrieve(BASEURL + path, full_path)
    return full_path
