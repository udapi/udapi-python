"""Block segment.Merge"""
from udapi.core.block import Block

class Merge(Block):
    """"Re-segmenter merging selected sentences (trees).

    This class merges sentences ending with semicolons,
    but it can be used as a base class for merging based on different criteria
    by overriding one of the `should_*` methods.
    """

    @staticmethod
    def should_merge_tokens(first, second):
        """Is there actually a sentence boundary between the first and second node?"""
        if first.form[-1] == ';':
            return True
        return False

    def should_merge_bundles(self, first_bundle, second_bundle):
        """Is there actually a sentence boundary between the first and second bundle?"""
        first_tree = self._get_our_tree(first_bundle)
        second_tree = self._get_our_tree(second_bundle)
        return self.should_merge_tokens(first_tree.descendants[-1], second_tree.descendants[0])


    def _get_our_tree(self, bundle):
        for tree in bundle:
            if self._should_process_tree(tree):
                return tree
        raise ValueError("Bundle %s contains no tree to process." % bundle.address())


    def process_document(self, doc):
        old_bundles = doc.bundles
        prev_bundle = old_bundles[0]
        new_bundles = [prev_bundle]
        for bundle in old_bundles[1:]:
            if self.should_merge_bundles(prev_bundle, bundle):
                for tree in bundle:
                    prev_tree = prev_bundle.get_tree(tree.zone)
                    prev_tree.steal_nodes(tree.descendants)
                    prev_tree.text = prev_tree.compute_text()
            else:
                new_bundles.append(bundle)
                prev_bundle = bundle
        doc.bundles = new_bundles