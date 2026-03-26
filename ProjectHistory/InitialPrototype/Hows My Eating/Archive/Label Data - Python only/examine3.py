import pandas as pd
import matplotlib.pyplot as plt

# Load CSV data
df = pd.read_csv('data/filtered_distances.csv')

# Remove rows with missing values
df.dropna(inplace=True)

# List of columns to analyze
df_columns = ['L0507', 'L0509', 'L0511', 'L0513', 'L0709',
              'L0711', 'L0713', 'L0911', 'L0913', 'L1113', 'L4955', 'L5258', 'L6257',
              'L6459', 'L6853', 'L6651', 'L0549', 'L0552', 'L0555', 'L0558', 'L0562',
              'L0564', 'L0566', 'L0568', 'L0749', 'L0752', 'L0755', 'L0758', 'L0762',
              'L0764', 'L0766', 'L0768', 'L0949', 'L0952', 'L0955', 'L0958', 'L0962',
              'L0964', 'L0966', 'L0968', 'L1149', 'L1152', 'L1155', 'L1158', 'L1162',
              'L1164', 'L1166', 'L1168', 'L1349', 'L1352', 'L1355', 'L1358', 'L1362',
              'L1364', 'L1366', 'L1368']

# Initialize a dictionary to store the results
change_details = {}

# Calculate statistics for each column
for column in df_columns:
    changes = df[column].diff()  # Calculate the difference between consecutive rows
    change_details[column] = {
        'Min': df[column].min(),
        'Max': df[column].max(),
        'Mean Change': changes.mean(),
        'Median Change': changes.median(),
        'Max Change': changes.max(),
        'Min Change': changes.min(),
        'Std Change': changes.std()
    }

# Convert the results into a DataFrame for better visualization
change_details_df = pd.DataFrame(change_details)

# Transpose the DataFrame to have columns as rows
change_details_df = change_details_df.T
df_filtered = df.iloc[1000:1300]


# Create a stacked area plot for L4955 and L5258
plt.figure(figsize=(10, 6))
plt.stackplot(df_filtered['Frame'], df_filtered['L4955'], df_filtered['L5258'], labels=['L4955', 'L5258'], alpha=0.7)

plt.title('Stacked Area Plot of L4955 and L5258 (Rows 1000 to 1541)')
plt.xlabel('Time (seconds)')
plt.ylabel('Value')
plt.legend(loc='upper left')
plt.grid(True)
plt.show()