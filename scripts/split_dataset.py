import os
import pandas as pd

# Path to dataset
dataset_path = '/Users/legue/dsp-loanprediction/model_training/loan_approval_data.csv'
raw_data_folder = '/Users/legue/dsp-loanprediction/data/raw_data'

# Ensure raw_data_folder exists
if not os.path.exists(raw_data_folder):
    os.makedirs(raw_data_folder)

def split_dataset(dataset_path, raw_data_folder, num_files):

    df = pd.read_csv(dataset_path)
    rows_per_file = len(df) // num_files
    
    for i in range(num_files):
        start_row = i * rows_per_file
        end_row = (i + 1) * rows_per_file if i != num_files - 1 else len(df)
        df_split = df.iloc[start_row:end_row]
        output_file = os.path.join(raw_data_folder, f'split_file_{i+1}.csv')
        df_split.to_csv(output_file, index=False)
        print(f"File {i+1} saved at: {output_file}")

        
        

    print(f"Dataset split into {num_files} files.")


split_dataset(dataset_path, raw_data_folder, 10)

