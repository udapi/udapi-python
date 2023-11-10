"""Wrapper for UDPipe online web service."""
import io
import sys
import email.mime.multipart
import email.mime.nonmultipart
import email.policy
import json
import os
import sys
import urllib.error
import urllib.request

from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.core.root import Root

class UDPipeOnline:
    """Wrapper for UDPipe online web service."""

    def __init__(self, model, server="https://lindat.mff.cuni.cz/services/udpipe/api"):
        """Create the UDPipeOnline tool object."""
        self.model = model
        self.server = server

    def list_models(self):
        with urllib.request.urlopen(self.server + "/models") as request:
            response = json.loads(request.read())
        return list(response["models"].keys())

    def perform_request(self, params, method="process"):
        if not params:
            request_headers, request_data = {}, None
        else:
            message = email.mime.multipart.MIMEMultipart("form-data", policy=email.policy.HTTP)

            for name, value in params.items():
                payload = email.mime.nonmultipart.MIMENonMultipart("text", "plain")
                payload.add_header("Content-Disposition", "form-data; name=\"{}\"".format(name))
                payload.add_header("Content-Transfer-Encoding", "8bit")
                payload.set_payload(value, charset="utf-8")
                message.attach(payload)

            request_data = message.as_bytes().split(b"\r\n\r\n", maxsplit=1)[1]
            request_headers = {"Content-Type": message["Content-Type"]}

        try:
            with urllib.request.urlopen(urllib.request.Request(
                url=f"{self.server}/{method}", headers=request_headers, data=request_data
            )) as request:
                response = json.loads(request.read())
        except urllib.error.HTTPError as e:
            print("An exception was raised during UDPipe 'process' REST request.\n"
                "The service returned the following error:\n"
                "  {}".format(e.fp.read().decode("utf-8")), file=sys.stderr)
            raise
        except json.JSONDecodeError as e:
            print("Cannot parse the JSON response of UDPipe 'process' REST request.\n"
                "  {}".format(e.msg), file=sys.stderr)
            raise

        if "model" not in response or "result" not in response:
            raise ValueError("Cannot parse the UDPipe 'process' REST request response.")

        return response["result"]

    def tag_parse_tree(self, root):
        """Tag (+lemmatize, fill FEATS) and parse a tree (already tokenized)."""
        descendants = root.descendants
        if not descendants:
            return
        in_data = " ".join([n.form for n in descendants])
        out_data = self.perform_request(params={"data": in_data, "input":"horizontal", "tagger":"", "parser":""})
        conllu_reader = ConlluReader()
        conllu_reader.files.filehandle = io.StringIO(out_data)
        parsed_root = conllu_reader.read_tree()
        root.flatten()
        for parsed_node in parsed_root.descendants:
            node = descendants[parsed_node.ord - 1]
            node.parent = descendants[parsed_node.parent.ord - 1] if parsed_node.parent.ord else root
            for attr in 'upos xpos lemma feats deprel'.split():
                setattr(node, attr, getattr(parsed_node, attr))

    def tokenize_tag_parse_tree(self, root, resegment=False, tag=True, parse=True):
        """Tokenize, tag (+lemmatize, fill FEATS) and parse the text stored in `root.text`.

        If resegment=True, the returned list of Udapi trees may contain multiple trees.
        """
        if parse and not tag:
            raise ValueError('Combination parse=True tag=False is not allowed.')
        if root.children:
            raise ValueError('Tree already contained nodes before tokenization')

        # Tokenize and possibly segment the input text
        params = {"model": self.model, "data": root.text, "tokenizer":"" if resegment else "presegmented"}
        if tag:
            params["tagger"] = ""
        if parse:
            params["parser"] = ""
        out_data = self.perform_request(params=params)
        conllu_reader = ConlluReader(empty_parent="ignore")
        conllu_reader.files.filehandle = io.StringIO(out_data)
        trees = conllu_reader.read_trees()

        # The input "root" object must be the first item in "trees".
        for attr in ('_children', '_descendants', '_mwts', 'text', 'comment'):
            setattr(root, attr, getattr(trees[0], attr))
        for node in root._children:
            node._parent = root
        for node in root._descendants:
            node._root = root
        trees[0] = root
        return trees

    def segment_text(self, text):
        """Segment the provided text into sentences returned as a Python list."""
        params = {"model": self.model, "data": text, "tokenizer":"", "output": "plaintext=normalized_spaces"}
        return self.perform_request(params=params).rstrip().split("\n")
