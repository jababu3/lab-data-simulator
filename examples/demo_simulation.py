from lab_data_simulator.simulators.plate_reader import PlateReader, PheraSTAR
from lab_data_simulator.simulators.liquid_handler import Echo
from lab_data_simulator.simulators.compound_reg import SDFGenerator
from lab_data_simulator.simulators.analytics.spr import SPRSimulator
from lab_data_simulator.simulators.analytics.purity import PuritySimulator
import pandas as pd
import os

def run_demo():
    print("=== Lab Data Simulator Demo ===")

    out_dir = 'output'
    os.makedirs(out_dir, exist_ok=True)
    print(f"\nCreated output directory: {os.path.abspath(out_dir)}")

    # 1. Simulate Echo Multi-Compound Dose-Response Picklist
    print("\n[1] Simulating Echo Multi-Compound Dose-Response Picklist...")
    echo = Echo(seed=42)

    compounds = [
        {'compound_id': 'CMP-00001', 'compound_name': 'Staurosporine',  'source_well': 'A1', 'concentration': 10000},
        {'compound_id': 'CMP-00002', 'compound_name': 'Gefitinib',      'source_well': 'A2', 'concentration': 10000},
        {'compound_id': 'CMP-00003', 'compound_name': 'Imatinib',       'source_well': 'A3', 'concentration': 10000},
        {'compound_id': 'CMP-00004', 'compound_name': 'Dasatinib',      'source_well': 'A4', 'concentration': 10000},
        {'compound_id': 'DMSO-CTL',  'compound_name': 'DMSO Control',   'source_well': 'P1', 'concentration': 0},
    ]

    picklist = echo.make_dose_response_picklist(
        compounds=compounds,
        source_plate='CPD_SRC_P001',
        dest_plate='ASSAY_PLATE_001',
        top_vol_nl=250.0,
        dilution_factor=3.0,
        n_points=8,
        n_replicates=2,
        failure_rate=0.08,   # ~8% failure rate
        volume_cv=0.03,      # 3% CV on acoustic dispense
        seed=42,
    )

    print(f"\nTotal transfers: {len(picklist)}")
    print(f"\nFirst 10 rows:")
    print(picklist.head(10).to_string(index=False))

    # Summary by status
    print("\nTransfer Status Summary:")
    print(picklist['Transfer Status'].value_counts().to_string())

    # Volume accuracy for successful transfers
    success = picklist[picklist['Transfer Status'] == 'Success']
    if not success.empty:
        pct_error = ((success['Actual Volume (nL)'] - success['Requested Volume (nL)'])
                     / success['Requested Volume (nL)'] * 100)
        print(f"\nVolume accuracy (successes only):")
        print(f"  Mean error : {pct_error.mean():.2f}%")
        print(f"  CV         : {pct_error.std():.2f}%")

    # Save to CSV
    out_path = os.path.join(out_dir, 'echo_transfer_log.csv')
    picklist.to_csv(out_path, index=False)
    print(f"\nSaved picklist to: {os.path.abspath(out_path)}")

    # 1.5 Generate Ground Truth Mapping
    print("\n[1.5] Generating Ground Truth 'Answer Key'...")
    ground_truth = {
        'CMP-00001': {'a': 100, 'b': 1.2, 'c': 0.5, 'd': 50000, 'noise': 1500},  # Potent (IC50 = 0.5 uM)
        'CMP-00002': {'a': 100, 'b': 0.8, 'c': 5.0, 'd': 50000, 'noise': 1000},  # Moderate (IC50 = 5.0 uM)
        'CMP-00003': {'a': 100, 'b': 1.0, 'c': 20.0, 'd': 50000, 'noise': 1200}, # Weak (IC50 = 20.0 uM)
        'CMP-00004': {'a': 100, 'b': 1.5, 'c': 0.05, 'd': 50000, 'noise': 2000}, # Very Potent (IC50 = 0.05 uM)
        'DMSO-CTL':  {'a': 50000, 'b': 1.0, 'c': 1.0, 'd': 50000, 'noise': 800}, # Flat max signal control
    }
    
    gt_df = pd.DataFrame.from_dict(ground_truth, orient='index')
    gt_df.index.name = 'Compound ID'
    gt_df.reset_index(inplace=True)
    gt_path = os.path.join(out_dir, 'ground_truth.csv')
    gt_df.to_csv(gt_path, index=False)
    print("Generated Ground Truth Mapping:")
    print(gt_df.to_string(index=False))
    print(f"Saved ground truth parameters to: {os.path.abspath(gt_path)}")
    
    # 2. Simulate Plate Read using Echo Picklist and Ground Truth
    print("\n[2] Simulating PheraSTAR Read (Picklist-Driven)...")
    reader = PheraSTAR()   # defaults to 384-well
    read_instructions = {
        'mode': 'picklist_driven',
        'params': {
            'picklist': picklist,
            'ground_truth': ground_truth,
            'assay_volume_nl': 50000.0, # 50 uL final assay volume
            'baseline': 100,
            'baseline_noise': 20
        }
    }
    result_df = reader.run_simulation(read_instructions)
    block = reader.to_block_format(result_df)
    print(f"Generated Plate Readout (block format, {len(result_df)} wells):")
    print(block.to_string(float_format=lambda x: f"{x:,.0f}"))
    
    # Save formatted report with headers
    report_path = os.path.join(out_dir, 'pherastar_readout.txt')
    reader.to_report(result_df, protocol_name='Demo Dose Response', output_path=report_path)
    print(f"\nSaved PHERAstar report with headers to: {os.path.abspath(report_path)}")

    # Save format report without headers
    raw_path = os.path.join(out_dir, 'pherastar_raw_data.txt')
    reader.to_report(result_df, include_header=False, output_path=raw_path)
    print(f"Saved PHERAstar report without headers to: {os.path.abspath(raw_path)}")
    
    # 3. Simulate Compound Registration
    print("\n[3] Simulating Compound Registration (SDF)...")
    sdf_gen = SDFGenerator()
    sdf_data = sdf_gen.run_simulation({'num_compounds': 3, 'prefix': 'DEMO'})
    print("Generated SDF Snippet:")
    print(sdf_data[:300] + "...") # Print first 300 chars
    
    # Save SDF output
    sdf_path = os.path.join(out_dir, 'demo_compounds.sdf')
    with open(sdf_path, 'w', encoding='utf-8') as f:
        f.write(sdf_data)
    print(f"\nSaved SDF file to: {os.path.abspath(sdf_path)}")
    
    # 4. Simulate Analytics (SPR)
    print("\n[4] Simulating SPR Results...")
    spr = SPRSimulator()
    spr_results = spr.run_simulation({'samples': ['DEMO1', 'DEMO2', 'DEMO3']})
    print("Generated SPR Data:")
    print(spr_results)

    # Save SPR Output
    spr_path = os.path.join(out_dir, 'spr_results.csv')
    spr_results.to_csv(spr_path, index=False)
    print(f"\nSaved SPR results to: {os.path.abspath(spr_path)}")

if __name__ == "__main__":
    run_demo()
