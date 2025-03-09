import sys
import time
from script import insert, query, mixed_requests
from reset_system import reset_all_nodes
from helpers import set_config
import os, csv
import matplotlib.pyplot as plt
import pandas as pd

def generate_charts():
    # Load data
    df = pd.read_csv('experiments/throughput_results.csv')
    
    # Filter data
    write_data = df[df['operation'] == 'write']
    read_data = df[df['operation'] == 'read']
    
    # Create figure
    plt.figure(figsize=(12, 6))
    
    # Write Throughput Chart
    plt.subplot(1, 2, 1)
    for consistency in ['strong', 'eventual']:
        subset = write_data[write_data['consistency'] == consistency]
        plt.plot(subset['k'], subset['throughput'], 
                label=f'Write ({consistency})', marker='o')
    plt.title('Write Throughput')
    plt.xlabel('Replication Factor (k)')
    plt.ylabel('Throughput (ops/sec)')
    plt.legend()
    
    # Read Throughput Chart
    plt.subplot(1, 2, 2)
    for consistency in ['strong', 'eventual']:
        subset = read_data[read_data['consistency'] == consistency]
        plt.plot(subset['k'], subset['throughput'], 
                label=f'Read ({consistency})', marker='o')
    plt.title('Read Throughput')
    plt.xlabel('Replication Factor (k)')
    plt.ylabel('Throughput (ops/sec)')
    plt.legend()
    
    # Save and show
    plt.tight_layout()
    plt.savefig('experiments/throughput_charts.png')
    plt.close()

def save_throughput(operation, config, throughput):
    """Save throughput results to a CSV file"""
    filename = "experiments/throughput_results.csv"
    file_exists = os.path.isfile(filename)
    mode = 'w' if not file_exists else 'a'
    
    with open(filename, mode) as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(['operation', 'k', 'consistency', 'throughput'])
        writer.writerow([operation, config['k'], config['consistency'], throughput])

def run_experiments():
    if os.path.exists('experiments/throughput_results.csv'):
        os.remove('experiments/throughput_results.csv')
    configs = [
        (1, True), (1, False),
        (3, True), (3, False),
        (5, True), (5, False)
    ]
    
    for k, consistency in configs:
        # Reset system
        print("\n=== Resetting system ===")
        reset_all_nodes()
        time.sleep(5)  # Allow time for reset propagation
        
        # Configure
        set_config(k, consistency)
        print(f"\nConfiguration: k={k}, consistency={'strong' if consistency else 'eventual'}")
        
        # Run insert experiment
        print("Running insert experiment...")
        insert_duration = insert()
        write_throughput = 500/insert_duration
        cons = 'strong' if consistency else 'eventual'
        save_throughput('write', {'k': k, 'consistency': cons}, write_throughput)
        print(f"Insert throughput: {write_throughput} ops/sec")
        
        # Run query experiment
        print("Running query experiment...")
        query_duration = query()
        read_throughput = 500/query_duration
        cons = 'strong' if consistency else 'eventual'
        save_throughput('read', {'k': k, 'consistency': cons}, read_throughput)
        print(f"Query throughput: {read_throughput} ops/sec")
        
    # Generate charts
    generate_charts()
    print("\nCharts saved to experiments/throughput_charts.png")

if __name__ == '__main__':
    run_experiments()