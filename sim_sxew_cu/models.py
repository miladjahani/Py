"""
Data models and type definitions for Copper SX-EW Simulation (SimSXEWCu v7.0).
Author: Joseph Kafumbila / Spark Autonomous Code Agent
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CircuitConfiguration(str, Enum):
    A1_2Ex1S = "A1_2Ex1S"          # Conventional 2Ex-1S without wash, EWB to leach
    A1_3Ex1S = "A1_3Ex1S"          # 3Ex-1S without wash, EWB to leach
    A1_ExPx1S = "A1_ExPx1S"        # Series-Parallel ExPx-1S without wash
    A2_2Ex1S = "A2_2Ex1S"          # 2Ex-1S without wash, EWB recycled to E1
    B1_2Ex1S = "B1_2Ex1S"          # 2Ex-1S with E1 Launder Wash (raw water)
    B2_2Ex1S = "B2_2Ex1S"          # 2Ex-1S Launder Wash with EWB & drain recycle to E1
    C1_2Ex1S = "C1_2Ex1S"          # 2Ex-1S dedicated Wash stage (raw water)
    C2_2Ex1S = "C2_2Ex1S"          # 2Ex-1S dedicated Wash with recycle to E1
    D1_2Ex1S = "D1_2Ex1S"          # 2Ex-1S Wash stage using acidulated water (Fe scrub)
    D2_2Ex1S = "D2_2Ex1S"          # 2Ex-1S Wash stage with acidulated water & recycle
    E1_2Ex1S = "E1_2Ex1S"          # 2Ex-1S Wash stage using diluted EWB (Fe scrub)
    E2_2Ex1S = "E2_2Ex1S"          # 2Ex-1S Wash stage using diluted EWB & recycle


@dataclass
class SolutionStream:
    name: str
    flow_m3h: float
    cu_gl: float = 0.0
    fe_total_gl: float = 0.0
    fe3_gl: float = 0.0
    fe2_gl: float = 0.0
    mn_gl: float = 0.0
    acid_gl: float = 0.0
    phase: str = "aqueous"  # "aqueous" or "organic"

    @property
    def cu_kg_h(self) -> float:
        return self.flow_m3h * self.cu_gl

    @property
    def fe_kg_h(self) -> float:
        return self.flow_m3h * (self.fe_total_gl or (self.fe3_gl + self.fe2_gl))

    @property
    def mn_kg_h(self) -> float:
        return self.flow_m3h * self.mn_gl

    @property
    def acid_kg_h(self) -> float:
        return self.flow_m3h * self.acid_gl


@dataclass
class PLSFeed:
    flow_m3h: float = 1000.0
    cu_gl: float = 2.50
    fe3_gl: float = 0.50
    fe2_gl: float = 2.00
    mn_gl: float = 4.00
    acid_gl: float = 5.00


@dataclass
class OperatingParams:
    extractant_type: str = "LIX984N"
    percent_ml: float = 80.0             # % to Maximum Loading
    oa_extraction: float = 1.25          # Organic to aqueous ratio on extraction
    mixing_eff_e1: float = 95.0
    mixing_eff_e2: float = 97.0
    mixing_eff_e3: float = 97.0
    mixing_eff_strip: float = 95.0
    mixing_eff_wash: float = 95.0
    target_advance_cu_gl: float = 50.0
    spent_cu_gl: float = 35.0
    spent_acid_gl: float = 190.0
    spent_cobalt_gl: float = 0.15
    current_density_a_m2: float = 300.0
    cathode_area_m2: float = 2.41
    cathodes_per_cell: int = 69
    ratio_cupr_sccupr: float = 5.0      # 20% scavenger production
    aq_entrainment_extraction: float = 2.0  # L/m3 organic
    aq_entrainment_coalescer: float = 1.0   # L/m3 organic
    aq_entrainment_lot: float = 0.8         # L/m3 organic
    aq_entrainment_strip: float = 1.0       # L/m3 organic
    org_entrainment_raffinate: float = 0.1  # L/m3 aqueous


@dataclass
class SimulationResults:
    config: CircuitConfiguration
    volume_percent_extractant: float
    max_loading_gl: float
    extraction_efficiency_percent: float
    copper_stripping_efficiency_percent: float
    iron_stripping_efficiency_percent: float
    manganese_wash_efficiency_percent: float
    iron_scrubbing_efficiency_percent: float
    copper_net_transfer_gl: float
    net_transfer_per_percent: float
    cu_fe_ratio_loaded_organic: float
    total_copper_production_th: float
    commercial_copper_production_th: float
    scavenger_copper_production_th: float
    number_of_commercial_cells: float
    number_of_scavenger_cells: float
    cell_amperage_ka: float
    ew_current_eff_commercial: float
    ew_current_eff_scavenger: float
    bleed_flow_m3h: float
    fe_mn_ratio_spent: float
    mn3_concentration_spent_gl: float
    mno4_concentration_spent_gl: float
    demin_water_consumption_m3_tcu: float
    raw_water_consumption_m3_tcu: float
    acid_consumption_ew_t_tcu: float
    cobalt_consumption_kg_tcu: float
    extractant_lost_kg_tcu: float
    diluent_lost_kg_tcu: float
    copper_lost_wbb_percent: float
    copper_in_bleed_ratio_percent: float
    global_copper_recovery_percent: float
    streams: Dict[str, SolutionStream] = field(default_factory=dict)
    summary_notes: List[str] = field(default_factory=list)
