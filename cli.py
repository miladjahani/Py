#!/usr/bin/env python3
"""
CLI Runner for SimSXEWCu v7.0 Copper SX-EW Simulation Engine.
Usage:
    python3 cli.py --config A1_2Ex1S --flow 1000 --cu 2.5
    python3 cli.py --config E1_2Ex1S --json
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sim_sxew_cu import (
    CircuitConfiguration,
    OperatingParams,
    PLSFeed,
    SXEWSimulator,
)


def main():
    parser = argparse.ArgumentParser(description="Copper SX-EW Simulation CLI (SimSXEWCu v7.0)")
    parser.add_argument("--config", type=str, default="A1_2Ex1S", help="Circuit configuration (A1_2Ex1S, A2_2Ex1S, B1_2Ex1S, C1_2Ex1S, D1_2Ex1S, E1_2Ex1S, etc.)")
    parser.add_argument("--flow", type=float, default=1000.0, help="PLS flow rate in m3/h (default: 1000)")
    parser.add_argument("--cu", type=float, default=2.50, help="PLS Cu concentration in g/L (default: 2.50)")
    parser.add_argument("--fe3", type=float, default=0.50, help="PLS Fe3+ concentration in g/L (default: 0.50)")
    parser.add_argument("--fe2", type=float, default=2.00, help="PLS Fe2+ concentration in g/L (default: 2.00)")
    parser.add_argument("--mn", type=float, default=4.00, help="PLS Mn concentration in g/L (default: 4.00)")
    parser.add_argument("--acid", type=float, default=5.00, help="PLS free acid concentration in g/L (default: 5.00)")
    parser.add_argument("--pml", type=float, default=80.0, help="Percentage to maximum loading %%ML (default: 80)")
    parser.add_argument("--oa", type=float, default=1.25, help="O/A ratio on extraction (default: 1.25)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    try:
        config = CircuitConfiguration(args.config)
    except ValueError:
        print(f"Error: Unknown configuration '{args.config}'. Available options:")
        for c in CircuitConfiguration:
            print(f"  - {c.value}")
        sys.exit(1)

    feed = PLSFeed(
        flow_m3h=args.flow,
        cu_gl=args.cu,
        fe3_gl=args.fe3,
        fe2_gl=args.fe2,
        mn_gl=args.mn,
        acid_gl=args.acid
    )
    params = OperatingParams(percent_ml=args.pml, oa_extraction=args.oa)

    sim = SXEWSimulator(feed, params)
    res = sim.simulate(config)

    if args.json:
        out = {
            "configuration": res.config.value,
            "volume_percent_extractant": res.volume_percent_extractant,
            "max_loading_gl": res.max_loading_gl,
            "extraction_efficiency_percent": res.extraction_efficiency_percent,
            "copper_stripping_efficiency_percent": res.copper_stripping_efficiency_percent,
            "iron_stripping_efficiency_percent": res.iron_stripping_efficiency_percent,
            "manganese_wash_efficiency_percent": res.manganese_wash_efficiency_percent,
            "iron_scrubbing_efficiency_percent": res.iron_scrubbing_efficiency_percent,
            "total_copper_production_th": res.total_copper_production_th,
            "commercial_copper_production_th": res.commercial_copper_production_th,
            "scavenger_copper_production_th": res.scavenger_copper_production_th,
            "commercial_cells_count": res.number_of_commercial_cells,
            "scavenger_cells_count": res.number_of_scavenger_cells,
            "cell_amperage_ka": res.cell_amperage_ka,
            "bleed_flow_m3h": res.bleed_flow_m3h,
            "fe_mn_ratio_spent": res.fe_mn_ratio_spent,
            "mn3_spent_gl": res.mn3_concentration_spent_gl,
            "mno4_spent_gl": res.mno4_concentration_spent_gl,
            "cu_fe_ratio_loaded_organic": res.cu_fe_ratio_loaded_organic,
            "extractant_loss_kg_tcu": res.extractant_lost_kg_tcu,
            "diluent_loss_kg_tcu": res.diluent_lost_kg_tcu,
            "demin_water_consumption_m3_tcu": res.demin_water_consumption_m3_tcu,
            "raw_water_consumption_m3_tcu": res.raw_water_consumption_m3_tcu,
            "acid_consumption_ew_t_tcu": res.acid_consumption_ew_t_tcu,
            "cobalt_consumption_kg_tcu": res.cobalt_consumption_kg_tcu,
            "global_copper_recovery_percent": res.global_copper_recovery_percent,
            "summary_notes": res.summary_notes,
            "streams": {k: {"flow_m3h": s.flow_m3h, "cu_gl": s.cu_gl, "fe_gl": s.fe_total_gl, "mn_gl": s.mn_gl, "acid_gl": s.acid_gl} for k, s in res.streams.items()}
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print("=" * 72)
    print(f" SIMULATION RESULTS: Copper SX-EW Simulator (SimSXEWCu v7.0)")
    print(f" Configuration: {res.config.value}")
    print("=" * 72)
    print(f" Feed PLS:               {args.flow:.1f} m3/h @ {args.cu:.2f} g/L Cu, {args.fe3:.2f} g/L Fe3+, {args.mn:.2f} g/L Mn")
    print(f" Extractant v/v%:        {res.volume_percent_extractant:.2f}% (Max Loading: {res.max_loading_gl:.2f} g/L Cu)")
    print(f" Extraction Efficiency:  {res.extraction_efficiency_percent:.2f}%")
    print(f" Global Cu Recovery:     {res.global_copper_recovery_percent:.2f}%")
    print(f" Total Cathode Output:   {res.total_copper_production_th:.3f} t/h ({res.total_copper_production_th*24:.2f} t/day)")
    print(f" Commercial Cells:       {res.number_of_commercial_cells:.1f} cells (Production: {res.commercial_copper_production_th:.3f} t/h)")
    print(f" Scavenger Cells:        {res.number_of_scavenger_cells:.1f} cells (Production: {res.scavenger_copper_production_th:.3f} t/h)")
    print(f" Cell Amperage:          {res.cell_amperage_ka:.2f} kA (Current Density: {params.current_density_a_m2} A/m2)")
    print(f" EW Bleed Flow Rate:     {res.bleed_flow_m3h:.2f} m3/h")
    print(f" Cu/Fe Ratio (LO):       {res.cu_fe_ratio_loaded_organic:.1f}")
    print(f" Fe/Mn Ratio (Spent):    {res.fe_mn_ratio_spent:.2f}")
    print(f" Mn(III) in Spent:       {res.mn3_concentration_spent_gl:.4f} g/L")
    print(f" MnO4- in Spent:         {res.mno4_concentration_spent_gl:.4f} g/L {'(CRITICAL RISK)' if res.mno4_concentration_spent_gl > 0.05 else '(SAFE)'}")
    print(f" Reagent Consumptions:")
    print(f"   - LIX 984N:           {res.extractant_lost_kg_tcu:.2f} kg / tCu")
    print(f"   - Diluent:            {res.diluent_lost_kg_tcu:.1f} kg / tCu")
    print(f"   - Demin Water:        {res.demin_water_consumption_m3_tcu:.2f} m3 / tCu")
    if res.raw_water_consumption_m3_tcu > 0:
        print(f"   - Raw Water (Wash):   {res.raw_water_consumption_m3_tcu:.2f} m3 / tCu")
    print(f"   - H2SO4 Makeup:       {res.acid_consumption_ew_t_tcu:.3f} t / tCu")
    print(f"   - Cobalt Sulfate:     {res.cobalt_consumption_kg_tcu*1000:.0f} g / tCu")
    print("-" * 72)
    print(" Key Streams:")
    for name, s in res.streams.items():
        print(f"   * {s.name:<25}: {s.flow_m3h:>7.1f} m3/h | Cu: {s.cu_gl:>6.3f} g/L | Fe: {s.fe_total_gl:>5.3f} g/L | Acid: {s.acid_gl:>5.1f} g/L")
    print("=" * 72)


if __name__ == "__main__":
    main()
