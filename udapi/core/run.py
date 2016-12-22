#!/usr/bin/env python3

import logging

from udapi.core.document import Document


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

        # Otherwise consider the token to be a block argument in the form key=value.
        logging.debug("- argument")

        # Test that there is only one '=' in the token.
        data_fields = token.split('=')
        if len(data_fields) != 2:
            raise ValueError('Invalid token %r', token)

        # Obtain key and value.
        attribute_name, attribute_value = token.split('=', 2)
        if number_of_blocks == 0:
            raise RuntimeError('Block attribute pair %r without a prior block name', token)

        # Put it as a new argument for the previous block
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
        module = "udapi.block." + sub_path + "." + class_name.lower()
        try:
            command = "from " + module + " import " + class_name + " as b" + str(block_id)
            logging.debug("Trying to run command: %s", command)
            exec(command)
        except:
            raise RuntimeError("Error when trying import the block %s", block_name)

        # Run the imported module.
        command = "b%s(block_args[block_id])" % block_id
        logging.debug("Trying to evaluate this: %s", command)
        new_block_instance = eval(command)
        blocks.append(new_block_instance)

    return blocks


class Run(object):
    """
    Processing unit that processes Universal Dependencies data; typically a sequence of blocks.

    """
    def __init__(self, args):
        """
        Initialization of the runner object.

        :param args: command line args as processed by argparser.

        """
        self.args = args
        if not isinstance(args.scenario, list):
            raise TypeError('Expected scenario as list, obtained a %r', args.scenario)

        if len(args.scenario) < 1:
            raise ValueError('Empty scenario')


    def run(self):
        """
        FIXME

        :return:

        """
        pass

    def execute(self):
        """
        Parse given scenario and execute it.

        """

        # Parse the given scenario from the command line.
        block_names, block_args = _parse_command_line_arguments(self.args.scenario)

        # Import blocks (classes) and construct block instances.
        blocks = _import_blocks(block_names, block_args)

        # Initialize blocks (process_start).
        for block in blocks:
            block.process_start()

        # Apply blocks on the data.
        readers = []
        for block in blocks:
            try:
                block.finished
                readers.append(block)
            except:
                pass

        finished = False
        while not finished:
            document = Document()
            logging.info(" ---- ROUND ----")
            for block in blocks:
                logging.info("Executing block " + block.__class__.__name__)
                block.process_document(document)

            finished = True

            for reader in readers:
                finished = finished and reader.finished

        # 6. close blocks (process_end)
        for block in blocks:
            block.process_end()
