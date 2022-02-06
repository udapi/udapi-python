"""Class Run parses a scenario and executes it."""
import logging

from udapi.core.document import Document
from udapi.block.read.conllu import Conllu


def _parse_block_name(block_name):
    """
    Obtain a path and the class name from the given block name.

    :return: A tuple path, class name.
    :rtype: tuple

    """
    # Obtain a list of names delimited by the '.' char.
    names = block_name.split('.')

    # Process trivial case with empty path.
    if len(names) == 1:
        return '', block_name

    # Return a path and the last name as a class name.
    return '.'.join(names[:-1]), names[-1]


def _parse_command_line_arguments(scenario):
    """
    Obtain a list of block names and a list of their arguments from the command line arguments list.

    :return: A tuple block names, block arguments.
    :rtype: tuple

    """
    block_names = []
    block_args = []

    number_of_blocks = 0
    for token in scenario:
        logging.debug("Token %s", token)

        # If there is no '=' character in the token, consider is as a block name.
        # Initialize the block arguments to an empty dict.
        if '=' not in token:
            logging.debug("- block name")
            block_names.append(token)
            block_args.append({})
            number_of_blocks += 1
            continue

        # Otherwise consider the token to be a block argument in the form
        # key=value.
        logging.debug("- argument")

        # The first '=' in the token separates name from value.
        # The value may contain other '=' characters (e.g. in util.Eval node='node.form = "_"').
        attribute_name, attribute_value = token.split('=', 1)
        if number_of_blocks == 0:
            raise RuntimeError(
                'Block attribute pair %r without a prior block name', token)

        # Put it as a new argument for the previous block
        if attribute_value.isdigit():
            attribute_value = int(attribute_value)
        block_args[-1][attribute_name] = attribute_value

    return block_names, block_args


def _import_blocks(block_names, block_args):
    """
    Parse block names, import particular packages and call the constructor for each object.

    :param block_names: A list of block names to be created.
    :param block_args: A list of block arguments to be passed to block constructor.
    :return: A list of initialized objects.
    :rtype: list

    """
    blocks = []

    for (block_id, block_name) in enumerate(block_names):
        # Importing module dynamically.
        sub_path, class_name = _parse_block_name(block_name)

        if block_name.startswith('.'):
            # Private modules are recognized by a dot at the beginning
            module = block_name.lower()[1:]
        else:
            module = "udapi.block." + sub_path + "." + class_name.lower()
        try:
            command = "from " + module + " import " + class_name + " as b" + str(block_id)
            logging.debug("Trying to run command: %s", command)
            exec(command)  # pylint: disable=exec-used
        except Exception:
            logging.warning("Error when trying import the block %s", block_name)
            raise

        # Run the imported module.
        kwargs = block_args[block_id]  # pylint: disable=unused-variable
        command = "b%s(**kwargs)" % block_id
        logging.debug("Trying to evaluate this: %s", command)
        new_block_instance = eval(command)  # pylint: disable=eval-used
        blocks.append((block_name, new_block_instance))

    return blocks


class Run(object):
    """Processing unit that processes UD data; typically a sequence of blocks."""

    def __init__(self, args):
        """Initialization of the runner object.

        :param args: command line args as processed by argparser.

        """
        self.args = args
        if not isinstance(args.scenario, list):
            raise TypeError(
                'Expected scenario as list, obtained a %r', args.scenario)

        if len(args.scenario) < 1:
            raise ValueError('Empty scenario')

    def execute(self):
        """Parse given scenario and execute it."""

        # Parse the given scenario from the command line.
        block_names, block_args = _parse_command_line_arguments(self.args.scenario)

        # Import blocks (classes) and construct block instances.
        blocks = _import_blocks(block_names, block_args)

        # Initialize blocks (process_start).
        for bname, block in blocks:
            block.process_start()

        readers = []
        for bname, block in blocks:
            try:
                block.finished  # pylint: disable=pointless-statement
                readers.append(block)
            except AttributeError:
                pass
        if not readers:
            logging.info('No reader specified, using read.Conllu')
            conllu_reader = Conllu()
            readers = [conllu_reader]
            blocks = [('read.Conllu', conllu_reader)] + blocks

        # Apply blocks on the data.
        finished = False
        while not finished:
            document = Document()
            logging.info(" ---- ROUND ----")
            for bname, block in blocks:
                logging.info(f"Executing block {bname}")
                block.apply_on_document(document)

            finished = True

            for reader in readers:
                finished = finished and reader.finished

        # 6. close blocks (process_end)
        for bname, block in blocks:
            block.process_end()

    # TODO: better implementation, included Scen
    def scenario_string(self):
        """Return the scenario string."""
        return "\n".join(self.args.scenario)


def create_block(block, **kwargs):
    """A factory function for creating new block instances (handy for IPython)."""
    blocks = _import_blocks([block], [kwargs])
    return blocks[0]
