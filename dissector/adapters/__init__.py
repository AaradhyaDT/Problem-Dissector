"""Adapters init file."""
from dissector.adapters.base import BaseCorpusAdapter, RawProblemData
from dissector.adapters.ieee_xtreme import IEEEXtremeAdapter

__all__ = ["BaseCorpusAdapter", "RawProblemData", "IEEEXtremeAdapter"]
