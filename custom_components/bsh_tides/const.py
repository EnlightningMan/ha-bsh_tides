"""Constants for the BSH Tides for Germany integration."""

from enum import Enum

DOMAIN = "bsh_tides"

class TideEvent(str, Enum):
    HIGH = "HW"
    LOW = "NW"
