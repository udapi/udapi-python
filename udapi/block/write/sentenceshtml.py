"""SentencesHtml class is a writer for sentences in HTML list (could be Google-translated, remembering sentence correspondence)."""
from udapi.core.basewriter import BaseWriter


class SentencesHtml(BaseWriter):
    """A writer of sentences in HTML list (one per item).

    Usage:
    udapy write.SentencesHtml if_missing=empty < my.conllu > my.html
    """

    def __init__(self, title='Sentences from CoNLL-U', if_missing='detokenize', **kwargs):
        """Create the SentencesHtml writer block.

        Parameters:
        if_missing: What to do if `root.text` is `None`? (default=detokenize)
         * `detokenize`: use `root.compute_text()` to compute the sentence.
         * `empty`: print an empty line
         * `warn_detokenize`, `warn_empty`: in addition emit a warning via `logging.warning()`
         * `fatal`: raise an exception
        """
        super().__init__(**kwargs)
        self.title = title
        self.if_missing = if_missing

    def before_process_document(self, document):
        super().before_process_document(document)
        print('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">')
        print('<title>' + self.title + '</title>')
        print('</head>\n<body>\n<ul>\n')

    def after_process_document(self, document):
        print("</ul>\n</body>\n</html>")
        super().after_process_document(document)

    def process_tree(self, tree):
        print('  <li id="%s">%s</li>' % (tree.sent_id, tree.get_sentence(self.if_missing)))
