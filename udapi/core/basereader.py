#!/usr/bin/env python

#from node import Node
#from bundle import Bundle
from block import Block

class BaseReader(Block):

    def __init__(self):
        self.finished = False

