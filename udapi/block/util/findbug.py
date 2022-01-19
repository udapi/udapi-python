"""Block util.FindBug for debugging.

Usage:
If block xy.Z fails with a Python exception,
insert "util.FindBug block=" into the scenario,
e.g. to debug ``second.Block``, use

  udapy first.Block util.FindBug block=second.Block > bug.conllu

This will create the file bug.conllu with the bundle, which caused the bug.

The second.Block can have any parameters, e.g.
  udapy first.Block util.FindBug block=second.Block param1=value1 param2=value2 > bug.conllu
"""
import copy
import logging

from udapi.core.basewriter import BaseWriter
from udapi.block.write.conllu import Conllu
from udapi.core.run import _parse_block_name


class FindBug(BaseWriter):
    """Debug another block by finding a minimal testcase conllu file."""

    def __init__(self, block, first_error_only=True,
                 files='-', filehandle=None, docname_as_file=False, encoding='utf-8',
                 newline='\n', overwrite=False,
                 **kwargs):
        """Args: block, first_error_only.
        All other parameters (which are not parameters of BaseWriter)
        will be passed to the block being inspected.
        """
        super().__init__(files, filehandle, docname_as_file, encoding, newline, overwrite)
        self.block = block
        self.first_error_only = first_error_only
        self._kwargs = kwargs

    def process_document(self, document):
        sub_path, class_name = _parse_block_name(self.block)
        module = "udapi.block." + sub_path + "." + class_name.lower()
        try:
            command = "from " + module + " import " + class_name + " as B"
            logging.debug("Trying to run command: %s", command)
            exec(command)  # pylint: disable=exec-used
        except Exception:
            logging.warning("Error when trying import the block %s", self.block)
            raise

        command = "B(**self._kwargs)"
        logging.debug("Trying to evaluate this: %s", command)
        new_block = eval(command)  # pylint: disable=eval-used

        doc_copy = copy.deepcopy(document)
        writer = Conllu(files=self.orig_files)

        for bundle_no, bundle in enumerate(doc_copy.bundles, 1):
            logging.debug('Block %s processing bundle #%d (id=%s)',
                          self.block, bundle_no, bundle.bundle_id)
            try:
                new_block.process_bundle(bundle)
            except Exception as exc:  # pylint: disable=broad-except
                logging.warning('util.FindBug found a problem in bundle %d in block %s: %r',
                                bundle_no, self.block, exc)
                logging.warning('Printing a minimal example to %s', self.orig_files)

                for tree in document.bundles[bundle_no - 1].trees:
                    writer.process_tree(tree)

                if self.first_error_only:
                    raise
