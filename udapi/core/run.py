#!/usr/bin/env python

#from node import Node
#from bundle import Bundle


from document import Document
from basereader import BaseReader
import re
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append( os.path.dirname(os.path.abspath(__file__)) + '/../../')

class Run(object):
    """Processing unit that processes Universal Dependencies data; typically a sequence of blocks."""

    def __init__(self, scenario_string="", command_line_argv=[]):
        self.scenario_string = scenario_string
        self.command_line_argv = command_line_argv


    def run(self):
        pass     
        

    def execute(self):

        block_names = []
        block_args = []

        # 1. parse scenario string

        number_of_blocks = 0

        for arg in self.command_line_argv[1:]:
            logging.info("token "+arg)
            if not '=' in arg:
                logging.info("Rozpoznan nazev bloku")
                block_names.append(arg)
                block_args.append({})
                number_of_blocks += 1
            else:
                logging.info("rozpoznan argument")
                attrname,attrvalue = arg.split('=',2)  # TODO: test for another '=' inside quotes 
                if (number_of_blocks == 0):
                    logging.info("block attribute pair "+arg+" without a prior block name") # TODO, dodelat, asi nahodit vyjimku
                    raise
                block_args[number_of_blocks-1][attrname] = attrvalue


        # 2. import blocks (classes) and construct block instances

        blocks = []

        for block_number in range(0,number_of_blocks):
            sub_path, class_name = ("."+block_names[block_number]).rsplit('.', 1)
            module = "udapi.block" + sub_path + "." + class_name.lower()
            try:
                command = "from " + module + " import " + class_name + " as b" + str(block_number)
                logging.info("Trying to run this: "+command)
                exec(command)
            except:
                logging.info("Error when trying import the block")
                raise
            
            command = "b"+str(block_number)+"(block_args[block_number])"
            logging.info("Trying to evaluate this: "+command)
            new_block_instance =  eval (command)
            blocks.append(new_block_instance)

        # 4. initialize blocks (process_start)
        for block in blocks:
            block.process_start()

        # 5. apply blocks on the data

        readers = []
        for block in blocks:
            try:
                block.finished
                readers.append(block)
            except:
                pass
            
        finished = False
        while not finished:
            document = Document
            logging.info(" ---- ROUND ----")
            for block in blocks:
                logging.info("        Executing block " + block.__class__.__name__)
                block.process_document(document)

            finished = True

            for reader in readers:
                finished = finished and reader.finished

        # 6. close blocks (process_end) 
        for block in blocks:
            block.process_end()

if __name__ == "__main__":

    runner = Run(command_line_argv = sys.argv )
    runner.execute()
