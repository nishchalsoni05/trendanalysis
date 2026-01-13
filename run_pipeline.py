"""
Project Aadhaar Sanket - Main Pipeline Runner

This script orchestrates the complete analytics pipeline:
1. Data Ingestion (CSV → Parquet)
2. Data Quality Validation
3. Signal Separation
4. MVI Calculation
5. Spatial Analysis
6. Anomaly Detection

Run this script to process all UIDAI data end-to-end.

Usage:
    python run_pipeline.py [--sample N]
    
    --sample N: Limit rows per file for testing (optional)
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import polars as pl

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Engines
from src.config import PARQUET_DIR, REPORTS_DIR, PROCESSED_FILES
from src.engines.ingestion import (
    run_ingestion_pipeline, 
    load_processed_dataset,
    save_dataset
)
from src.engines.quality import validate_dataset, print_quality_report, save_quality_report
from src.engines.signal_separation import (
    apply_signal_weights,
    generate_signal_report,
    print_signal_report,
)
from src.engines.mvi import (
    calculate_mvi, 
    calculate_population_base,
    calculate_rolling_mvi,
    generate_mvi_summary,
    print_mvi_report,
    get_top_mvi_regions,
)
from src.engines.spatial import (
    add_zone_classification,
    detect_hotspot_clusters,
    aggregate_by_state,
    generate_spatial_summary,
    print_spatial_summary
)
from src.engines.anomaly import (
    detect_mvi_anomalies,
    classify_anomaly_pattern,
    contextualize_anomalies,
    generate_anomaly_report,
    print_anomaly_report,
    generate_alerts
)
from src.engines.trend_typology import (
    analyze_trend_typology,
    generate_typology_summary,
    print_typology_summary
)
from src.engines.persistence_analysis import (
    analyze_persistence,
    generate_persistence_summary,
    print_persistence_summary
)
from src.engines.trend_acceleration import (
    analyze_acceleration,
    generate_acceleration_summary,
    print_acceleration_summary
)
from src.engines.seasonality_detector import (
    analyze_seasonality,
    generate_seasonality_summary,
    print_seasonality_summary
)
from src.engines.population_impact import (
    analyze_population_impact,
    generate_impact_summary,
    print_impact_summary
)
from src.engines.trend_confidence import (
    analyze_trend_confidence,
    generate_confidence_summary,
    print_confidence_summary
)
from src.engines.policy_mapper import (
    generate_policy_recommendations,
    generate_policy_summary,
    print_policy_summary
)
from src.engines.insight_generator import (
    generate_insights,
    print_insights,
    export_insights_to_json
)


def print_banner():
    """Print the project banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗║
║     ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝║
║     ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║   ║
║     ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║   ║
║     ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║   ║
║     ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝   ║
║                                                               ║
║                   AADHAAR SANKET                              ║
║           Demographic Intelligence System                     ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_full_pipeline(sample_size: int = None) -> dict:
    """
    Execute the complete analytics pipeline.
    
    Args:
        sample_size: Optional row limit per file for testing
        
    Returns:
        Pipeline execution summary
    """
    start_time = datetime.now()
    results = {
        "pipeline_start": start_time.isoformat(),
        "stages": {},
        "success": True,
    }
    
    print_banner()
    
    # =========================================================================
    # STAGE 1: DATA INGESTION
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 1: DATA INGESTION")
    print("═" * 70)
    
    try:
        ingestion_summary = run_ingestion_pipeline(sample_size=sample_size)
        results["stages"]["ingestion"] = {
            "status": "SUCCESS",
            "datasets": list(ingestion_summary["datasets"].keys()),
            "total_rows": sum(
                d["row_count"] for d in ingestion_summary["datasets"].values()
            ),
        }
        print("\n✓ Ingestion completed successfully")
    except Exception as e:
        results["stages"]["ingestion"] = {"status": "FAILED", "error": str(e)}
        results["success"] = False
        print(f"\n✗ Ingestion failed: {e}")
        return results
    
    # =========================================================================
    # STAGE 2: DATA QUALITY VALIDATION
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 2: DATA QUALITY VALIDATION")
    print("═" * 70)
    
    quality_results = {}
    
    for dataset_type in ["biometric", "demographic", "enrolment"]:
        try:
            df = load_processed_dataset(dataset_type)
            passes, report = validate_dataset(df, dataset_type)
            print_quality_report(report)
            save_quality_report(report)
            
            quality_results[dataset_type] = {
                "status": "PASS" if passes else "FAIL",
                "score": report.overall_score,
            }
        except Exception as e:
            quality_results[dataset_type] = {"status": "ERROR", "error": str(e)}
    
    results["stages"]["quality"] = quality_results
    print("\n✓ Quality validation completed")
    
    # =========================================================================
    # STAGE 3: SIGNAL SEPARATION
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 3: SIGNAL SEPARATION")
    print("═" * 70)
    
    try:
        # Process demographic data with signal separation
        demographic_df = load_processed_dataset("demographic")
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        
        signal_report = generate_signal_report(demographic_df, "demographic")
        print_signal_report(signal_report)
        
        # Process biometric data
        biometric_df = load_processed_dataset("biometric")
        biometric_df = apply_signal_weights(biometric_df, "biometric")
        
        bio_signal_report = generate_signal_report(biometric_df, "biometric")
        print_signal_report(bio_signal_report)
        
        results["stages"]["signal_separation"] = {
            "status": "SUCCESS",
            "demographic_noise_removed": signal_report["summary"]["noise_percent"],
            "biometric_noise_removed": bio_signal_report["summary"]["noise_percent"],
        }
        print("\n✓ Signal separation completed")
    except Exception as e:
        results["stages"]["signal_separation"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ Signal separation failed: {e}")
    
    # =========================================================================
    # STAGE 4: MVI CALCULATION
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 4: MIGRATION VELOCITY INDEX (MVI)")
    print("═" * 70)
    
    try:
        # Load enrolment for population base
        enrolment_df = load_processed_dataset("enrolment")
        population_df = calculate_population_base(enrolment_df, "district")
        
        # Calculate MVI (Snapshot)
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        
        # Calculate MVI (Time Series) for Trend Analytics
        mvi_ts_df = calculate_rolling_mvi(demographic_df, population_df, "district")
        
        # Generate summary (Snapshot)
        mvi_summary = generate_mvi_summary(mvi_df)
        print_mvi_report(mvi_summary)
        
        # Show top regions
        print("\nTOP 10 HIGH-PRESSURE REGIONS:")
        print("-" * 60)
        top_regions = get_top_mvi_regions(mvi_df, 10)
        for i, row in enumerate(top_regions.to_dicts(), 1):
            district = row.get('district', 'N/A')
            state = row.get('state', 'N/A')
            mvi = row.get('mvi', 0)
            band = row.get('mvi_band', 'N/A')
            print(f"  {i}. {district}, {state}: MVI={mvi:.2f} [{band}]")
        
        results["stages"]["mvi"] = {
            "status": "SUCCESS",
            "total_units": mvi_summary["total_units"],
            "mean_mvi": mvi_summary["mvi_statistics"]["mean"],
            "high_pressure_count": mvi_summary["interpretation"]["high_pressure_count"],
        }
        print("\n✓ MVI calculation completed")
        
    except Exception as e:
        results["stages"]["mvi"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ MVI calculation failed: {e}")
    
    # =========================================================================
    # STAGE 5: SPATIAL ANALYSIS
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 5: SPATIAL ANALYSIS")
    print("═" * 70)
    
    try:
        # Add zone classification
        mvi_df = add_zone_classification(mvi_df)
        
        # Detect clusters
        mvi_df = detect_hotspot_clusters(mvi_df)
        
        # Generate spatial summary
        spatial_summary = generate_spatial_summary(mvi_df)
        print_spatial_summary(spatial_summary)
        
        # State-level aggregation
        state_df = aggregate_by_state(mvi_df)
        
        print("\nSTATE-LEVEL SUMMARY:")
        print("-" * 60)
        for row in state_df.sort("mvi", descending=True).head(10).to_dicts():
            print(f"  {row['state']}: MVI={row.get('mvi', 0):.2f}")
        
        results["stages"]["spatial"] = {
            "status": "SUCCESS",
            "zone_distribution": spatial_summary["zone_distribution"],
            "states_covered": spatial_summary["unique_states"],
        }
        print("\n✓ Spatial analysis completed")
        
    except Exception as e:
        results["stages"]["spatial"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ Spatial analysis failed: {e}")
    
    # =========================================================================
    # STAGE 6: ANOMALY DETECTION
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 6: ANOMALY DETECTION")
    print("═" * 70)
    
    try:
        # Detect anomalies
        anomaly_df = detect_mvi_anomalies(mvi_df)
        
        # Generate report
        anomaly_report = generate_anomaly_report(anomaly_df)
        print_anomaly_report(anomaly_report)
        
        # Generate alerts
        alerts = generate_alerts(anomaly_df)
        
        if alerts:
            print(f"\n⚠ {len(alerts)} alerts generated")
            for alert in alerts[:3]:  # Show top 3
                print(f"  - {alert.severity}: {alert.title}")
        else:
            print("\n✓ No anomalies requiring immediate attention")
        
        results["stages"]["anomaly"] = {
            "status": "SUCCESS",
            "anomaly_count": anomaly_report["summary"]["anomaly_count"],
            "risk_level": anomaly_report["interpretation"]["risk_level"],
            "alerts_generated": len(alerts),
        }
        print("\n✓ Anomaly detection completed")
        
    except Exception as e:
        results["stages"]["anomaly"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ Anomaly detection failed: {e}")
    
    # =========================================================================
    # STAGE 7: ADVANCED TREND ANALYTICS (PHASE 1 & 2)
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 7: ADVANCED TREND ANALYTICS (TYPOLOGY, PERSISTENCE, IMPACT)")
    print("═" * 70)

    try:
        # 7a. Trend Typology
        typology_df = analyze_trend_typology(mvi_ts_df)
        save_dataset(typology_df, "trend_typology")
        print_typology_summary(generate_typology_summary(typology_df))
        
        # 7b. Persistence Analysis
        persistence_df = analyze_persistence(mvi_ts_df)
        save_dataset(persistence_df, "trend_persistence")
        print_persistence_summary(generate_persistence_summary(persistence_df))
        
        # 7c. Trend Acceleration
        acceleration_df = analyze_acceleration(mvi_ts_df)
        save_dataset(acceleration_df, "acceleration")
        print_acceleration_summary(generate_acceleration_summary(acceleration_df))
        
        # 7d. Seasonality
        seasonality_df = analyze_seasonality(mvi_ts_df)
        save_dataset(seasonality_df, "seasonality")
        print_seasonality_summary(generate_seasonality_summary(seasonality_df))

        # 7e. Population Impact
        impact_df = analyze_population_impact(mvi_ts_df, population_df)
        save_dataset(impact_df, "population_impact")
        print_impact_summary(generate_impact_summary(impact_df))
        
        # 7f. Contextualize Anomalies
        # Re-run anomaly detection with context
        anomaly_context_df = contextualize_anomalies(anomaly_df, persistence_df)
        save_dataset(anomaly_context_df, "anomalies") # Overwrite with enhanced
        
        results["stages"]["trend_analytics"] = {"status": "SUCCESS"}
        print("\n✓ Advanced trend analytics completed")

    except Exception as e:
        results["stages"]["trend_analytics"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ Advanced trend analytics failed: {e}")

    # =========================================================================
    # STAGE 8: DECISION INTELLIGENCE (PHASE 3 & 4)
    # =========================================================================
    print("\n" + "═" * 70)
    print("STAGE 8: DECISION INTELLIGENCE (CONFIDENCE, POLICY, INSIGHTS)")
    print("═" * 70)

    try:
        # 8a. Trend Confidence
        confidence_df = analyze_trend_confidence(mvi_ts_df)
        save_dataset(confidence_df, "trend_confidence")
        print_confidence_summary(generate_confidence_summary(confidence_df))
        
        # 8b. Policy Recommendations
        policy_df = generate_policy_recommendations(
            typology_df, impact_df, confidence_df, seasonality_df, acceleration_df
        )
        save_dataset(policy_df, "policy_recommendations")
        print_policy_summary(generate_policy_summary(policy_df))
        
        # 8c. Insight Generation
        insights_df = generate_insights(
            typology_df, persistence_df, impact_df, confidence_df, 
            acceleration_df, seasonality_df, policy_df
        )
        save_dataset(insights_df, "insights")
        
        # Export JSON for frontend
        export_insights_to_json(insights_df, PROCESSED_FILES["insights_json"])
        
        print_insights(insights_df, limit=5)
        
        results["stages"]["decision_intelligence"] = {"status": "SUCCESS"}
        print("\n✓ Decision intelligence generation completed")

    except Exception as e:
        results["stages"]["decision_intelligence"] = {"status": "FAILED", "error": str(e)}
        print(f"\n✗ Decision intelligence failed: {e}")

    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results["pipeline_end"] = end_time.isoformat()
    results["duration_seconds"] = duration
    
    print("\n" + "═" * 70)
    print("PIPELINE EXECUTION COMPLETE")
    print("═" * 70)
    print(f"\nTotal Duration: {duration:.1f} seconds")
    print(f"Overall Status: {'SUCCESS' if results['success'] else 'FAILED'}")
    
    # Stage summary
    print("\nStage Summary:")
    for stage, info in results["stages"].items():
        status = info.get("status", "UNKNOWN")
        symbol = "✓" if status in ["SUCCESS", "PASS"] else "✗"
        print(f"  {symbol} {stage.upper()}: {status}")
    
    # Save results
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = REPORTS_DIR / "pipeline_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_path}")
    
    print("\n" + "═" * 70)
    
    return results


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Aadhaar Sanket - Demographic Intelligence Pipeline"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit rows per file for testing (optional)"
    )
    
    args = parser.parse_args()
    
    results = run_full_pipeline(sample_size=args.sample)
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
