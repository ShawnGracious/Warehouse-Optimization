"""
Warehouse Capacity Planner - Configuration & Data Models

Areas: 600 Paper | 400 Consumables | 300 Cust.Specific 1 | 200 Cust.Specific 2 | 100 Final
Volume is calculated from rack dimensions: L × D × H × num_racks

Flow rules:
  600 → 300 or 200 (paper split per order)
  400 → 300 or 200 (customer split per order)
  300 / 200 → 100 Final (packout)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Zone definitions
# ---------------------------------------------------------------------------
ZONE_NAMES: Dict[str, str] = {
    "600": "Paper",
    "400": "Consumables",
    "300": "Customer Specific 1",
    "200": "Customer Specific 2",
    "100": "Final (ready to ship)",
}

ZONE_FLOW_ORDER = ["600", "400", "300", "200", "100"]


# ---------------------------------------------------------------------------
# StorageArea — volume derived from rack dimensions
# ---------------------------------------------------------------------------
@dataclass
class StorageArea:
    id: str
    name: str
    zone: str
    # Rack dimensions (in the current display unit, stored in cu ft internally)
    rack_length_cuft: float       # length of one rack (cu ft)
    rack_depth_cuft:  float       # depth of one rack (cu ft)
    rack_height_cuft: float       # height of one rack (cu ft)
    num_racks:        int          # number of racks in this area
    efficiency:       float        # usable fraction 0–1
    units_per_box:      float      # avg units per box in this area
    box_length_cuft:    float      # box length (cu ft)
    box_depth_cuft:     float      # box depth  (cu ft)
    box_height_cuft:    float      # box height (cu ft)
    max_concurrent_boxes: Optional[int] = None  # hard cap; None = use volume

    @property
    def avg_box_size_cuft(self) -> float:
        """Box volume = L × D × H."""
        return self.box_length_cuft * self.box_depth_cuft * self.box_height_cuft

    @property
    def volume_cuft(self) -> float:
        """Total cubic feet = L × D × H × num_racks."""
        return self.rack_length_cuft * self.rack_depth_cuft * self.rack_height_cuft * self.num_racks

    @property
    def rack_volume_cuft(self) -> float:
        """Volume of a single rack."""
        return self.rack_length_cuft * self.rack_depth_cuft * self.rack_height_cuft

    @property
    def capacity_boxes(self) -> int:
        vol_cap = int((self.volume_cuft * self.efficiency) / self.avg_box_size_cuft)
        if self.max_concurrent_boxes is not None:
            return min(self.max_concurrent_boxes, vol_cap)
        return vol_cap

    @property
    def capacity_units(self) -> int:
        return int(self.capacity_boxes * self.units_per_box)

    @property
    def has_box_cap(self) -> bool:
        return self.max_concurrent_boxes is not None

    def utilization_pct(self, load_boxes: float) -> float:
        cap = self.capacity_boxes
        return (load_boxes / cap * 100) if cap > 0 else 0.0

    def status(self, load_boxes: float) -> str:
        pct = self.utilization_pct(load_boxes)
        if pct >= 100: return "OVER CAPACITY"
        if pct >= 85:  return "CRITICAL"
        if pct >= 70:  return "WARNING"
        return "OK"


# ---------------------------------------------------------------------------
# Order splits
# ---------------------------------------------------------------------------
@dataclass
class StorageSplit:
    """Split 1 — paper_pct + consumable_pct = 100."""
    paper_pct:      float = 50.0
    consumable_pct: float = 50.0


@dataclass
class CustomerSplit:
    """Split 2 — cust1_pct + cust2_pct = 100 (applied to consumable portion)."""
    cust1_pct: float = 60.0
    cust2_pct: float = 40.0


@dataclass
class KittingSplit:
    """Split 3 — packout_pct + kitting_pct = 100 (of 300/200 material)."""
    packout_pct: float = 70.0
    kitting_pct: float = 30.0


# ---------------------------------------------------------------------------
# OrderType
# ---------------------------------------------------------------------------
@dataclass
class OrderType:
    id: str
    name: str
    daily_volume: int
    avg_units_per_order: int
    storage_split:  StorageSplit  = field(default_factory=StorageSplit)
    customer_split: CustomerSplit = field(default_factory=CustomerSplit)
    kitting_split:  KittingSplit  = field(default_factory=KittingSplit)

    def total_units(self, multiplier: float = 1.0) -> float:
        return self.daily_volume * multiplier * self.avg_units_per_order

    def units_paper(self, multiplier: float = 1.0) -> float:
        return self.total_units(multiplier) * (self.storage_split.paper_pct / 100)

    def units_consumable(self, multiplier: float = 1.0) -> float:
        return self.total_units(multiplier) * (self.storage_split.consumable_pct / 100)

    def units_cust1(self, multiplier: float = 1.0) -> float:
        return self.units_consumable(multiplier) * (self.customer_split.cust1_pct / 100)

    def units_cust2(self, multiplier: float = 1.0) -> float:
        return self.units_consumable(multiplier) * (self.customer_split.cust2_pct / 100)

    def boxes_in_area(self, area: "StorageArea", multiplier: float = 1.0) -> float:
        """Boxes placed in a given area based on zone routing."""
        if area.zone == "600":
            units = self.units_paper(multiplier)
        elif area.zone == "400":
            units = self.units_consumable(multiplier)
        elif area.zone == "300":
            units = self.units_cust1(multiplier)
        elif area.zone == "200":
            units = self.units_cust2(multiplier)
        else:
            units = 0.0
        return units / area.units_per_box if area.units_per_box > 0 else 0.0


# ---------------------------------------------------------------------------
# Default areas  (5 areas, rack dimensions in cu ft)
# Typical rack: 4ft L × 2ft D × 8ft H = 64 cu ft per rack
# ---------------------------------------------------------------------------
DEFAULT_AREAS: List[StorageArea] = [
    StorageArea(
        id="zone600", name="600 – Paper", zone="600",
        rack_length_cuft=4.0, rack_depth_cuft=2.0, rack_height_cuft=8.0,
        num_racks=56, efficiency=0.70,
        box_length_cuft=1.5, box_depth_cuft=1.5, box_height_cuft=2.2, units_per_box=24.0,
    ),
    StorageArea(
        id="zone400", name="400 – Consumables", zone="400",
        rack_length_cuft=4.0, rack_depth_cuft=2.0, rack_height_cuft=8.0,
        num_racks=44, efficiency=0.75,
        box_length_cuft=1.2, box_depth_cuft=1.2, box_height_cuft=2.4, units_per_box=12.0,
    ),
    StorageArea(
        id="zone300", name="300 – Customer Specific 1", zone="300",
        rack_length_cuft=4.0, rack_depth_cuft=2.0, rack_height_cuft=8.0,
        num_racks=28, efficiency=0.80,
        box_length_cuft=1.0, box_depth_cuft=1.0, box_height_cuft=2.5, units_per_box=8.0,
    ),
    StorageArea(
        id="zone200", name="200 – Customer Specific 2", zone="200",
        rack_length_cuft=4.0, rack_depth_cuft=2.0, rack_height_cuft=8.0,
        num_racks=28, efficiency=0.80,
        box_length_cuft=1.0, box_depth_cuft=1.0, box_height_cuft=2.5, units_per_box=8.0,
    ),
    StorageArea(
        id="packout", name="Packout – Final Assembly", zone="100",
        rack_length_cuft=4.0, rack_depth_cuft=2.0, rack_height_cuft=6.0,
        num_racks=19, efficiency=0.85,
        box_length_cuft=1.0, box_depth_cuft=1.0, box_height_cuft=1.5, units_per_box=6.0,
    ),
]

# ---------------------------------------------------------------------------
# Default order types
# ---------------------------------------------------------------------------
DEFAULT_ORDER_TYPES: List[OrderType] = [
    OrderType(
        id="SO", name="SO – Standard Order",
        daily_volume=120, avg_units_per_order=50,
        storage_split=StorageSplit(paper_pct=40.0, consumable_pct=60.0),
        customer_split=CustomerSplit(cust1_pct=60.0, cust2_pct=40.0),
        kitting_split=KittingSplit(packout_pct=70.0, kitting_pct=30.0),
    ),
    OrderType(
        id="SW", name="SW – Special Warehouse",
        daily_volume=40, avg_units_per_order=35,
        storage_split=StorageSplit(paper_pct=20.0, consumable_pct=80.0),
        customer_split=CustomerSplit(cust1_pct=50.0, cust2_pct=50.0),
        kitting_split=KittingSplit(packout_pct=50.0, kitting_pct=50.0),
    ),
    OrderType(
        id="BW", name="BW – Bulk Warehouse",
        daily_volume=25, avg_units_per_order=120,
        storage_split=StorageSplit(paper_pct=60.0, consumable_pct=40.0),
        customer_split=CustomerSplit(cust1_pct=70.0, cust2_pct=30.0),
        kitting_split=KittingSplit(packout_pct=80.0, kitting_pct=20.0),
    ),
]
