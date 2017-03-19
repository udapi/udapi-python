"""Block udpipe.En for tagging and parsing English."""
from udapi.block.udpipe.base import Base


class En(Base):
    """Tag and parse English."""

    def __init__(self, **kwargs):
        """Create the udpipe.En block object."""
        super().__init__(model_alias='en', **kwargs)
