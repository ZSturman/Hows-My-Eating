import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Load the manually labeled data
manual_df = pd.read_csv('step6.csv')

# Load the OpenCV-generated features
features_df = pd.read_csv('step1.csv')

# Merge the datasets on 'frame'
merged_df = pd.merge(features_df, manual_df[['frame', 'teeth', 'lips', 'action']], on='frame')

# Initialize LabelEncoders for each target variable
le_teeth = LabelEncoder()
le_lips = LabelEncoder()
le_action = LabelEncoder()

# Encode the labels
merged_df['teeth_encoded'] = le_teeth.fit_transform(merged_df['teeth'])
merged_df['lips_encoded'] = le_lips.fit_transform(merged_df['lips'])
merged_df['action_encoded'] = le_action.fit_transform(merged_df['action'])

# Define features (X) and target variables (y)
X = merged_df.drop(columns=['frame', 'timestamp', 'teeth', 'lips', 'action', 'teeth_encoded', 'lips_encoded', 'action_encoded'])
y_teeth = merged_df['teeth_encoded']
y_lips = merged_df['lips_encoded']
y_action = merged_df['action_encoded']

# Save the feature order (column names)
feature_order = X.columns.tolist()

# Split the data for each target variable
X_train_teeth, X_test_teeth, y_train_teeth, y_test_teeth = train_test_split(X, y_teeth, test_size=0.2, random_state=42)
X_train_lips, X_test_lips, y_train_lips, y_test_lips = train_test_split(X, y_lips, test_size=0.2, random_state=42)
X_train_action, X_test_action, y_train_action, y_test_action = train_test_split(X, y_action, test_size=0.2, random_state=42)

# Initialize the classifiers
clf_teeth = RandomForestClassifier(random_state=42)
clf_lips = RandomForestClassifier(random_state=42)
clf_action = RandomForestClassifier(random_state=42)

# Train the classifiers
clf_teeth.fit(X_train_teeth, y_train_teeth)
clf_lips.fit(X_train_lips, y_train_lips)
clf_action.fit(X_train_action, y_train_action)

# Predict and evaluate for teeth
y_pred_teeth = clf_teeth.predict(X_test_teeth)
print("Classification Report for Teeth:")
print(classification_report(y_test_teeth, y_pred_teeth, target_names=le_teeth.classes_))

# Predict and evaluate for lips
y_pred_lips = clf_lips.predict(X_test_lips)
print("\nClassification Report for Lips:")
print(classification_report(y_test_lips, y_pred_lips, target_names=le_lips.classes_))

# Predict and evaluate for action
y_pred_action = clf_action.predict(X_test_action)
print("\nClassification Report for Action:")
print(classification_report(y_test_action, y_pred_action, target_names=le_action.classes_))

# Save the models to disk
joblib.dump(clf_teeth, 'clf_teeth.pkl')
joblib.dump(clf_lips, 'clf_lips.pkl')
joblib.dump(clf_action, 'clf_action.pkl')

# Save the label encoders to disk
joblib.dump(le_teeth, 'le_teeth.pkl')
joblib.dump(le_lips, 'le_lips.pkl')
joblib.dump(le_action, 'le_action.pkl')

# Save the feature order to disk
joblib.dump(feature_order, 'feature_order.pkl')
