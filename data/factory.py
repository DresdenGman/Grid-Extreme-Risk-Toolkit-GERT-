"""
Factory function to get the appropriate data adapter for a region.
"""

from typing import Optional

from data.base import GridDataAdapter
from data.ercot import ERCOTAdapter
from data.caiso import CAISOAdapter
from data.pjm import PJMAdapter
from data.nyiso import NYISOAdapter


def get_data_adapter(region: str) -> GridDataAdapter:
    """
    Get the appropriate data adapter for a given region.
    
    Args:
        region: ISO region identifier (e.g., "ERCOT_NORTH", "CAISO")
        
    Returns:
        GridDataAdapter instance for the region
        
    Raises:
        ValueError: If region is not supported
    """
    region_upper = region.upper()
    
    if region_upper.startswith("ERCOT"):
        return ERCOTAdapter()
    elif region_upper == "CAISO":
        return CAISOAdapter()
    elif region_upper == "PJM":
        return PJMAdapter()
    elif region_upper == "NYISO":
        return NYISOAdapter()
    else:
        # Default to ERCOT for unknown regions
        return ERCOTAdapter()
