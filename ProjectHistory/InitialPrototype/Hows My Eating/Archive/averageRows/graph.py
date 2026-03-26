import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy import stats
import json

def rank_columns_with_percentages(chew_df, not_chew_df, features, output_file):
    """
    Rank columns based on T-Test and Mann-Whitney U test results, calculate percentages for ranking, and output results as JSON.
    """
    test_results = []

    for feature in features:
        # Perform T-Test
        t_stat, t_p_val = stats.ttest_ind(chew_df[feature], not_chew_df[feature], equal_var=False)
        
        # Perform Mann-Whitney U Test
        u_stat, u_p_val = stats.mannwhitneyu(chew_df[feature], not_chew_df[feature], alternative='two-sided')
        
        test_results.append({
            "feature": feature,
            "t_stat": abs(t_stat),  # Use absolute value for ranking
            "t_p_val": t_p_val,
            "u_stat": u_stat,
            "u_p_val": u_p_val
        })

    # Sort by the most significant p-values first (t-test followed by U-test)
    ranked_results = sorted(test_results, key=lambda x: (x["t_p_val"], x["u_p_val"], -x["t_stat"]))

    # Calculate percentages based on t-stat values
    total_t_stat = sum(result["t_stat"] for result in ranked_results if result["t_stat"] is not None)
    for result in ranked_results:
        result["importance_percentage"] = (result["t_stat"] / total_t_stat) * 100 if total_t_stat != 0 else 0

    # Save the ranked results with percentages to a JSON file
    with open(output_file, "w") as f:
        json.dump(ranked_results, f, indent=4)

    print(f"Rankings with percentages saved to {output_file}")

def load_data(video_chew_path, video_not_chew_path, motion_chew_path, motion_not_chew_path):
    """
    Load CSV files into dataframes.
    """
    video_chew_df = pd.read_csv(video_chew_path)
    video_not_chew_df = pd.read_csv(video_not_chew_path)
    motion_chew_df = pd.read_csv(motion_chew_path)
    motion_not_chew_df = pd.read_csv(motion_not_chew_path)
    
    return video_chew_df, video_not_chew_df, motion_chew_df, motion_not_chew_df

def remove_null_and_outliers(df, columns):
    """
    Remove rows with null, zero, or NaN values and extreme outliers in specified columns.
    """
    print(f"Original data shape: {df.shape}")
    print("Columns", columns)
    print("DF", df.head())
    # Remove null or NaN values
    df = df.dropna(subset=columns)
    
    # Remove zero values
    for col in columns:
        df = df[df[col] != 0]
    
    # Remove outliers using the 1.5*IQR rule
    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    
    return df

def vizualize_data(df, features):
    """
    Visualize data distributions using boxplots and correlation matrices.
    """
    # Plot feature distributions
    for feature in features:
        plt.figure(figsize=(8, 6))
        sns.boxplot(x='Label', y=feature, data=df)
        plt.title(f'Video Feature: {feature} Distribution by Label')
        plt.xlabel('Label')
        plt.ylabel(feature)
        plt.show()

def compare_data(chew, not_chew, features, label_chew="Chew", label_not_chew="Not-Chew"):
    """
    Visualize video data distributions using boxplots and correlation matrices.
    """
    # Combine data for visualization
    combined_data = pd.concat([
        chew[features].assign(Label=label_chew),
        not_chew[features].assign(Label=label_not_chew)
    ])

    # Plot feature distributions
    #vizualize_data(combined_data, features)

    # Correlation matrices
    chew_corr = chew[features].corr()
    not_chew_corr = not_chew[features].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(chew_corr, annot=True, cmap="coolwarm")
    plt.title('Correlation Matrix: Video Features (Chew)')
    plt.show()

    plt.figure(figsize=(10, 8))
    sns.heatmap(not_chew_corr, annot=True, cmap="coolwarm")
    plt.title('Correlation Matrix: Video Features (Not-Chew)')
    plt.show()


def rank_columns_by_tests(chew_df, not_chew_df, features, output_file):
    """
    Rank columns based on T-Test and Mann-Whitney U test results, and output the results as JSON.
    """
    test_results = []

    for feature in features:
        # Perform T-Test
        t_stat, t_p_val = stats.ttest_ind(chew_df[feature], not_chew_df[feature], equal_var=False)
        
        # Perform Mann-Whitney U Test
        u_stat, u_p_val = stats.mannwhitneyu(chew_df[feature], not_chew_df[feature], alternative='two-sided')
        
        test_results.append({
            "feature": feature, 
            "t_stat": t_stat,
            "t_p_val": t_p_val,
            "u_stat": u_stat,
            "u_p_val": u_p_val
        })

    # Sort the results by the lowest p-value (indicating stronger differences)
    ranked_results = sorted(test_results, key=lambda x: (x["t_p_val"], x["u_p_val"]))

    # Save the ranked results to a JSON file
    with open(output_file, "w") as f:
        json.dump(ranked_results, f, indent=4)

    print(f"Test results have been saved to {output_file}")
    
    
# Example usage
# Replace these paths with the actual absolute paths of your CSV files
# video_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_chunk_data_chew.csv"
# video_not_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_chunk_data_not_chew.csv"
# motion_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_motion_data_chew.csv"
# motion_not_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_motion_data_not_chew.csv"

video_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_chunk_data_chew2.csv"
video_not_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_chunk_data_not_chew2.csv"
motion_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_motion_data_chew2.csv"
motion_not_chew_path = "/Users/zacharysturman/Desktop/export/aggregated_motion_data_not_chew2.csv"

# Load the data
video_chew_df, video_not_chew_df, motion_chew_df, motion_not_chew_df = load_data(
    video_chew_path, video_not_chew_path, motion_chew_path, motion_not_chew_path
)

video_chew_df_cols = video_chew_df.columns
video_not_chew_df_cols = video_not_chew_df.columns

# Combine the video columns lists and remove duplicates
video_cols = list(set(video_chew_df_cols) | set(video_not_chew_df_cols))

# Remove all columsn that start with "frame", "p", "interval", "timestamp"
video_cols = [col for col in video_cols if not col.startswith(('frame', 'p', 'timestamp', 'file', 'interval','mouth_open_ratio', 'last_row_mouth', 'middle_row_action', 'middle_row_mouth', 'last_row_behind_hand', 'first_row_behind_hand', 'last_row_action', 'first_row_action', 'first_row_mouth', 'middle_row_behind_hand', 'middle_row_mouth', 'first_row', 'diff_middle_to_last_p', 'diff_first_to_middle_p', 'middle_row', 'last_row'))]
video_cols = [col for col in video_cols if not col.endswith(('min', 'max', 'hand', 'frame', 'label', 'timestamp', 'action'))]
video_chew_df = remove_null_and_outliers(video_chew_df, video_cols)
video_not_chew_df = remove_null_and_outliers(video_not_chew_df, video_cols)

motion_chew_df_cols = motion_chew_df.columns
motion_not_chew_df_cols = motion_not_chew_df.columns

# Combine the motion columns lists and remove duplicates
motion_cols = list(set(motion_chew_df_cols) | set(motion_not_chew_df_cols))

# Remove all columns that start with "timestamp"
motion_cols = [col for col in motion_cols if not col.startswith(('timestamp', 'file', 'interval', 'first_row', 'middle_row', 'last_row'))]
motion_cols = [col for col in motion_cols if not col.endswith(('min', 'max', 'file_path', 'timestamp', 'label'))]
motion_chew_df = remove_null_and_outliers(motion_chew_df, motion_cols)
motion_not_chew_df = remove_null_and_outliers(motion_not_chew_df, motion_cols)

output_json_path = "/Users/zacharysturman/Desktop/export/video_column_rankings.json"
#rank_columns_by_tests(video_chew_df, video_not_chew_df, video_cols, output_json_path)
rank_columns_with_percentages(video_chew_df, video_not_chew_df, video_cols, output_json_path)

output_json_path = "/Users/zacharysturman/Desktop/export/motion_column_rankings.json"
#rank_columns_by_tests(motion_chew_df, motion_not_chew_df, motion_cols, output_json_path)
rank_columns_with_percentages(motion_chew_df, motion_not_chew_df, motion_cols, output_json_path)

 