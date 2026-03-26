import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('features_and_lengths.csv')

df.replace(-1, pd.NA, inplace=True)
df.interpolate(method='linear', inplace=True)

""" plt.figure(figsize=(12, 6))
plt.plot(df['Timestamp'], df['L4955'], label='L4955')
plt.plot(df['Timestamp'], df['L5258'], label='L5258')
plt.legend()
plt.show() """

print(df['L4955'].describe())



df['L4955_diff'] = df['L4955'].diff()
df['L5258_diff'] = df['L5258'].diff()

#mouth_opening = (df['L5258_diff'] > threshold_opening) & (df['L4955_diff'] < -threshold_narrowing)
#mouth_closing = (df['L5258_diff'] < -threshold_closing) & (df['L4955_diff'] > threshold_widening)

# print(df['L4955'].diff())
# print(df['L5258'].diff())

""" 
from scipy.signal import find_peaks

peaks, _ = find_peaks(df['L5258'], distance=minimum_chew_distance)
chew_peaks = df.iloc[peaks]

mouth_opening = (df['L5258_diff'] > threshold_opening) & (df['L4955_diff'] < -threshold_narrowing)
mouth_closing = (df['L5258_diff'] < -threshold_closing) & (df['L4955_diff'] > threshold_widening)

df['is_mouth_opening'] = mouth_opening & df['behindHand']
df['is_mouth_closing'] = mouth_closing & df['behindHand']

chew_count = 0
df['chew_count'] = 0

bite_detected = False

for idx, row in df.iterrows():
    if row['is_mouth_opening'] and not bite_detected:
        bite_detected = True
        chew_count = 1
        df.at[idx, 'Label'] = 'mouthOpening, newBite'
    elif row['is_mouth_closing'] and bite_detected:
        df.at[idx, 'Label'] = 'mouthClosing, newBite'
    elif row['is_mouth_opening'] and bite_detected:
        chew_count += 1
        df.at[idx, 'chew_count'] = chew_count
        df.at[idx, 'Label'] = f'mouthOpening, chew{chew_count}'
    elif row['is_mouth_closing'] and bite_detected:
        df.at[idx, 'Label'] = f'mouthClosing, chew{chew_count}'
        
        
from sklearn.ensemble import RandomForestClassifier

features = df[['L4955', 'L5258', 'L0958', 'L0513']].fillna(0)
labels = df['Label']  # You need a labeled dataset for this

model = RandomForestClassifier()
model.fit(features, labels)

df['PredictedLabel'] = model.predict(features) """