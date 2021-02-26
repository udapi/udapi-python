from udapi.core.block import Block
from collections import Counter
import re

class MiscStatsTex(Block):
    """Block corefud.MiscStats prints 10 most frequent values of each attribute stored in the MISC field"""

    def __init__(self, maxvalues=10, **kwargs):
        
        """Create the corefud.MiscStats

        Args:
        maxvalues: the number of most frequent values
                   to be printed for each attribute.

        """
        super().__init__(**kwargs)
        self.maxvalues = maxvalues
        self.valuecounter = {}
        self.totalcounter = Counter()

    def process_node(self,node):
        for attrname in node.misc:
            shortattrname = re.sub(r'\[\d+\]',r'',attrname)
            if not shortattrname in self.valuecounter:
                self.valuecounter[shortattrname] = Counter()
            self.valuecounter[shortattrname][node.misc[attrname]] += 1
            self.totalcounter[shortattrname] += 1

    def process_end(self):
        for attrname in self.valuecounter:

            total = self.totalcounter[attrname]
            distrvalues = []
            
            for value,freq in self.valuecounter[attrname].most_common(self.maxvalues):
                value = re.sub(r'_',r'\\_',value)
                distrvalues.append(f'\\attr{{{str(value)}}} {100*freq/total:2.1f}~\\%')

            attrname = re.sub(r'_',r'\\_',attrname)
            print(f" \\item attribute \\attr{{{attrname}}}, {total:,} occurrences, values: "+", ".join(distrvalues))     
#            print(f" \\item attribute \\attr\{{attrname}\}, {str(total)} occurrences, distribution of values: "+", ".join(distrvalues))

                
