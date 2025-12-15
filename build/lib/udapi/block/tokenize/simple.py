"""Block tokenize.Simple"""
import re

from udapi.block.tokenize.onwhitespace import OnWhitespace


class Simple(OnWhitespace):
    """Simple tokenizer, splits on whitespaces and punctuation, fills SpaceAfter=No."""

    @staticmethod
    def tokenize_sentence(string):
        """A method to be overriden in subclasses."""
        return re.findall(r'\w+|[^\w\s]', string)
