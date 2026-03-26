import json
import pandas as pd
from typing import Optional

def merge_labels(
    dirpath: str,
    labels_json: str,
    mov_info_json: str,
    merged_csv_output_name: str,
    logger
) -> Optional[str]:
    """
    Merge label data with movie information, fill in missing frames, correct intermittent labeling errors,
    and compute cumulative bite and chew counts along with the chews per bite ratio. The final merged DataFrame
    is saved as a CSV file.

    This function assumes that the label data now contains:
      - mouth: "Open" | "Closed"
      - action: "Bite" | "Chew" | "Swallow" | "Other"

    The cumulative counts are incremented when there is a transition in the mouth state from 'Closed' to 'Open'
    and the corresponding action is either 'Bite' or 'Chew'. Additionally, if the labeled JSON provides no values,
    the first row is defaulted to mouth = "Closed" and action = "Other". Finally, if the very first row shows action="Bite"
    with an "Open" mouth, the bite_count is incremented by 1.

    Args:
        labels_json (str): Path to the JSON file containing label data.
        mov_info_json (str): Path to the JSON file containing movie metadata.
        merged_csv_output_name (str): Base name for the output CSV file (without extension).
        logger: Logger instance for logging messages.

    Returns:
        Optional[str]: The path to the saved CSV file if successful; otherwise, None.
    """
    try:
        # Load JSON data
        with open(labels_json, 'r') as f:
            labels = json.load(f)
        with open(mov_info_json, 'r') as f:
            mov_info = json.load(f)

        total_frames = mov_info.get('total_frames')
        logger.info(f"Starting merge_labels: {len(labels)} labels, total_frames={total_frames}")

        # Create DataFrame from labels and sort by timestamp
        df = pd.DataFrame(labels)
        df = df.sort_values(by='timestamp')

        # Remove duplicate frames, keeping the one with the largest id, and drop unused columns
        df = df.drop_duplicates(subset='frame', keep='last')
        df = df.drop(columns=['id', 'timestamp'])

        # Create a DataFrame with a full range of frames
        full_frame_range = pd.DataFrame({'frame': range(1, total_frames + 1)})

        # Merge to include all frames (left join)
        df_full = pd.merge(full_frame_range, df, on='frame', how='left')

        # If the very first row is missing a value for 'mouth' or 'action', set defaults.
        if pd.isna(df_full.loc[0, 'mouth']):
            df_full.loc[0, 'mouth'] = 'Closed'
        if pd.isna(df_full.loc[0, 'action']):
            df_full.loc[0, 'action'] = 'Other'

        # Forward-fill the missing values so that every row has values for mouth and action.
        df_full.fillna(method='ffill', inplace=True)
        df_full = df_full.reset_index(drop=True)

        # Correct isolated mislabels for 'mouth' and 'action'
        for i in range(1, len(df_full) - 1):
            for col in ['mouth', 'action']:
                prev_value = df_full.at[i - 1, col]
                curr_value = df_full.at[i, col]
                next_value = df_full.at[i + 1, col]
                if prev_value == next_value and curr_value != prev_value:
                    df_full.at[i, col] = prev_value

        # Compute cumulative bite and chew counts.
        df_full['bite_count'] = 0
        df_full['chew_count'] = 0
        bite_count = 0
        chew_count = 0

        # Special-case: if the very first row already indicates an Open mouth with action "Bite",
        # assume the previous (implicit) state was closed and count this as the first bite.
        if isinstance(df_full.loc[0, 'mouth'], str) and df_full.loc[0, 'mouth'].lower() == 'open':
            if df_full.loc[0, 'action'] == 'Bite':
                bite_count = 1
                df_full.at[0, 'bite_count'] = bite_count

        # Loop through the frames starting from the second row.
        for i in range(1, len(df_full)):
            prev_row = df_full.iloc[i - 1]
            curr_row = df_full.iloc[i]
            # Check for a mouth state transition from 'Closed' to 'Open'
            if (
                isinstance(prev_row['mouth'], str) and prev_row['mouth'].lower() == 'closed' and
                isinstance(curr_row['mouth'], str) and curr_row['mouth'].lower() == 'open'
            ):
                if curr_row['action'] == 'Bite':
                    bite_count += 1
                elif curr_row['action'] == 'Chew':
                    chew_count += 1
            df_full.at[i, 'bite_count'] = bite_count
            df_full.at[i, 'chew_count'] = chew_count

        # Compute chews per bite ratio for each frame (set to 0 if no bites have occurred)
        df_full['chews_per_bite'] = df_full.apply(
            lambda row: row['chew_count'] / row['bite_count'] if row['bite_count'] != 0 else 0,
            axis=1
        )

        # Save the merged DataFrame to a CSV file at dirpath/merged_csv_output_name.csv
        output_file = f"{dirpath}/{merged_csv_output_name}.csv"
        df_full.to_csv(output_file, index=False)
        logger.info(f"Merged CSV saved to {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"Error in merge_labels: {e}", exc_info=True)
        return None