def get_node_representation(node, print_lemma=False):
    """
    Transform the node into the proper textual representation,
    as will appear in the extracted contexts.

    :param node: An input Node.
    :param print_lemma: If true, the node lemma is used, otherwise the node form.
    :return: A proper node textual representation for the contexts data.

    """
    if print_lemma:
        output = node.lemma
    else:
        output = node.form

    output = output.lower()
    return output


def print_triple(node_a, relation_name, node_b, print_lemma=False):
    """
    Print to the standard output the context.

    """
    # Extract the requested nodes representations.
    node_a = get_node_representation(node_a, print_lemma=print_lemma)
    node_b = get_node_representation(node_b, print_lemma=print_lemma)

    context = u"%s %s_%s" % (node_a, relation_name, node_b)
    print(context)
