"""Block udpipe.Cs for tagging and parsing Czech."""
from udapi.block.udpipe.base import Base


class Cs(Base):
    """Tag and parse Czech."""

    def __init__(self, **kwargs):
        """Create the udpipe.Cs block object."""
        super().__init__(model_alias='cs', **kwargs)
