

**Chew Tracker ML Pipeline**

  

- Get audio & motion data in the same sample rate
- Normalize features to have zero mean
- Audio features -> MFCCs, zero-crossing rate, spectral
- Motion features -> mean acceleration, angular velocity, pitch
- Create time series -> align properly
- Correlate -> Pearson correlation coefficient

  

  

**Audio Feature Extraction**

  

- MFCCs
- ZCR
- Spectral Centroid

  

  

  

**Audio ML Features**

  

When collecting and retrieving data from an audio file for machine learning purposes, you can extract a variety of features. These features can be broadly categorized into several types:

  

### 1. **Basic Audio Properties**

- **Sampling Rate**: The number of samples per second.

- **Bit Depth**: The number of bits used to represent each sample.

- **Duration**: The length of the audio file.

  

### 2. **Temporal Features**

- **Zero Crossing Rate**: The rate at which the signal changes sign.

- **Energy**: The sum of squared amplitudes.

- **Entropy of Energy**: The entropy of sub-frames' normalized energies.

- **Temporal Centroid**: The center of mass of the waveform.

  

### 3. **Frequency Domain Features**

- **Spectral Centroid**: The center of mass of the spectrum.

- **Spectral Bandwidth**: The width of the spectrum.

- **Spectral Contrast**: The difference in amplitude between peaks and valleys in a spectrum.

- **Spectral Flatness**: The measure of how flat the spectrum is.

- **Spectral Rolloff**: The frequency below which a certain percentage of the total spectral energy lies.

  

### 4. **Cepstral Features**

- **Mel-Frequency Cepstral Coefficients (MFCCs)**: Coefficients that represent the short-term power spectrum of a sound.

- **Chroma Features**: Energy distribution across the 12 different pitch classes.

- **Mel Spectrogram**: A spectrogram with frequencies converted to the Mel scale.

  

### 5. **Rhythm Features**

- **Tempo**: The speed of the beat.

- **Beat**: The regular rhythm or pulse of the audio.

  

### 6. **Harmonic Features**

- **Harmonic-to-Noise Ratio (HNR)**: The ratio of harmonic to noise energy.

- **Tonnetz (Tonal Centroid Features)**: Features representing the harmonic content.

  

### 7. **Formant Features**

- **Formant Frequencies**: The resonant frequencies of the vocal tract.

- **Bandwidths of Formants**: The width of each formant.

  

### 8. **Voice Quality Features**

- **Jitter**: The frequency variation from cycle to cycle.

- **Shimmer**: The amplitude variation from cycle to cycle.

- **Harmonics-to-Noise Ratio (HNR)**: The ratio of harmonics to noise.

  

### 9. **Additional Features**

- **Autocorrelation**: A measure of similarity between observations as a function of the time




**Chew Counter**

  

### Summary of the Paper "Automatic Measurement of Chew Count and Chewing Rate during Food Intake"

  

**1. Abstract:**

The study explores the automatic measurement of chew count and chewing rate using a piezoelectric sensor system. The method was tested on 120 meals from 30 participants. Results showed no significant difference between manual and automatic chew counts, suggesting the method's effectiveness in objectively quantifying eating behavior.

  

**2. Introduction:**

The introduction discusses the importance of studying eating behaviors to address obesity and eating disorders. Traditional methods rely on self-reporting, which is often inaccurate. The paper highlights the need for objective and automatic methods to measure chew count and chewing rate.

  

**3. Methods:**

This section outlines the study's data collection protocol, sensor system, annotation process, and the development of the chew counting algorithm. The methods include both semi-automatic and fully automatic approaches for chew count estimation.

  

**4. Results:**

The results section presents data on chew counts and chewing rates for different meals. It compares the performance of the semi-automatic and fully automatic methods, showing mean absolute errors of 10.4% and 15.0%, respectively. The results indicate that the proposed method can accurately estimate chew counts.

  

**5. Discussion:**

The discussion highlights the strengths and limitations of the study. The method was tested on a large population with a variety of foods, making it robust. The paper suggests improvements for future studies, such as participant-dependent calibration and testing in free-living conditions.

  

**6. Conclusions:**

The study concludes that the proposed method can automatically detect and quantify chewing behavior accurately. The authors suggest further exploration and testing in real-world conditions.

  

**7. Acknowledgments and References:**

The paper acknowledges the support from the National Institute of Diabetes and Digestive and Kidney Diseases and lists the references used throughout the study.

  

Would you like more detailed information on any specific section?

  

### Details on the Sensors

  

**Sensor System and Annotation:**

  

1. **Sensor Description:**

   - The study used a commercially available piezoelectric film sensor (LDT0-028K) from Measurement Specialties Inc.

   - This sensor was placed below the ear using a medical adhesive to capture lower jaw movements during chewing.

  

2. **Sensor Specifications:**

   - The sensor consists of a piezoelectric PVDF polymer film (28-μm thickness) with screen-printed Ag-ink electrodes encapsulated in a polyester substrate (0.125-mm thickness).

   - It has a sensitivity of 10 mV per micro-strains, sufficient to detect skin surface vibrations caused by chewing.

  

3. **Signal Processing:**

   - Sensor signals were buffered using a custom-designed amplifier with an input impedance of about 10 MΩ.

   - Signals in the range of 0-2 V were sampled at 44,100 Hz with a 16-bit resolution data acquisition device (USB-160HS-2AO from Measurement Computing) and stored in computer memory.

  

4. **Data Annotation:**

   - Experiments were videotaped and time-synchronized with sensor signals.

   - Custom-built software was used to annotate videos and sensor signals, marking start and end of each eating event, including bites, chewing, and swallows.

   - The annotated data was used for algorithm development and validation.

  

5. **Signal Processing for Chew Count:**

   - Signals were demeaned and filtered with a low-pass filter (cutoff of 3 Hz) to remove noise.

   - A histogram-based peak detection algorithm was used to identify chews, considering only peaks above a certain threshold to avoid motion artifacts.

  

Would you like more technical details or information on another aspect of the sensors?

  

### Technical Details of the Sensor System

  

**Sensor Specifications:**

- **Type**: Piezoelectric film sensor (LDT0-028K, Measurement Specialties Inc.)

- **Material**: PVDF polymer film (28-μm thickness)

- **Electrodes**: Screen-printed Ag-ink

- **Substrate**: Polyester (0.125-mm thickness)

- **Sensitivity**: 10 mV per micro-strains

- **Attachment**: Medical adhesive below the ear

  

**Signal Processing:**

1. **Amplification**: Custom-designed amplifier with input impedance of about 10 MΩ.

2. **Sampling**:

   - **Range**: 0-2 V

   - **Frequency**: 44,100 Hz

   - **Resolution**: 16 bits

  

**Data Collection and Annotation:**

- **Annotation Software**: Custom-built LabVIEW software

- **Video Synchronization**: PS3Eye camera, synchronized with sensor signals

- **Annotation Details**: Human raters marked start and end of eating events (bites, chews, swallows)

  

**Signal Processing for Chew Detection:**

1. **Demeaning**: Subtract mean amplitude to account for offset drift.

2. **Filtering**: Low-pass filter with a cutoff of 3 Hz to remove noise.

3. **Peak Detection**: Histogram-based approach to select peaks above a threshold to avoid motion artifacts.

4. **Smoothing**: Moving average filter (100 samples) to smooth signal variations.

  

**Algorithms:**

1. **Chew Counting**: Number of peaks in the signal estimates the number of chews.

2. **Epoch-Based Classification**:

   - Signals split into 5-second epochs.

   - ANN used to classify epochs as “food intake” or “no intake” with features computed from the sensor data.

  

**Performance Evaluation:**

- **Manual vs. Automatic**: Compared against manually annotated chew counts.

- **Error Metrics**: Mean absolute error and mean signed error were reported to evaluate performance.

  

Would you like to know more about the algorithm or the performance results?

  

### Chew Counting Algorithm

  

**Overview:**

The chew counting algorithm processes the sensor signals to detect and count chewing events. It uses a combination of signal filtering, peak detection, and smoothing techniques. The algorithm operates in two approaches: semi-automatic and fully automatic.

  

**Steps Involved:**

  

1. **Signal Preprocessing:**

   - **Demeaning:** Subtract the mean amplitude from the sensor signals to correct for offset drift.

   - **Filtering:** Apply a low-pass filter with a cutoff frequency of 3 Hz to eliminate noise, retaining the frequency range of chewing motions (0.94 to 2 Hz).

  

2. **Peak Detection:**

   - **Histogram-Based Threshold Selection:** Use a histogram of signal amplitudes to determine a peak detection threshold. This threshold is selected based on the upper percentile (αth percentile) of signal amplitudes, ensuring that only significant peaks (representing chews) are considered.

   - **Thresholding:** Identify peaks in the filtered signal that exceed the selected threshold.

  

3. **Smoothing:**

   - **Moving Average Filter:** Apply a moving average filter with a window size of 100 samples to smooth the signal and reduce the effect of small amplitude variations.

  

4. **Chew Counting:**

   - **Peak Counting:** Count the number of peaks in the smoothed signal, which corresponds to the number of chews.

  

**Approaches:**

  

1. **Semi-Automatic Approach:**

   - **Manual Segmentation:** Use manually annotated chewing segments for chew counting.

   - **Threshold Adaptation:** Adapt the peak detection threshold based on signal amplitude variations in the annotated segments.

   - **Error Calculation:** Compute errors by comparing estimated chew counts with manual counts.

  

2. **Fully Automatic Approach:**

   - **Epoch-Based Segmentation:** Divide the sensor signals into 5-second epochs.

   - **Feature Extraction:** Compute 38 time and frequency domain features for each epoch.

   - **Classification:** Use an Artificial Neural Network (ANN) to classify epochs as "food intake" or "no intake" based on extracted features.

   - **Chew Counting:** Apply the chew counting algorithm to epochs classified as food intake.

  

**ANN Classification:**

- **Architecture:** Three-layer feed-forward ANN with:

  - Input Layer: 38 neurons (one for each feature)

  - Hidden Layer: 5 neurons (determined through cross-validation)

  - Output Layer: 1 neuron (indicating food intake or no intake)

- **Training and Validation:** Leave-one-out cross-validation to train and validate the ANN models.

  

**Performance Metrics:**

- **F1 Score:** Measure of classifier performance, combining precision and recall.

- **Mean Absolute Error:** Average absolute difference between estimated and true chew counts.

- **Signed Error:** Average signed difference to indicate overestimation or underestimation trends.

  

This algorithm provides a robust method for automatic chew counting and rate estimation, essential for studying ingestive behavior and its implications on health.

  

### Replicating the Chew Counting Algorithm with AirPods

  

To replicate the chew counting algorithm using AirPods, which can collect both audio and motion data, follow these steps:

  

1. **Data Collection:**

   - **Audio Data:** Use the built-in microphones to capture chewing sounds.

   - **Motion Data:** Utilize the accelerometer and gyroscope to detect jaw movements.

  

2. **Signal Preprocessing:**

   - **Audio Filtering:** Apply noise reduction and low-pass filtering to isolate chewing sounds.

   - **Motion Data Filtering:** Apply similar filtering to the accelerometer and gyroscope data to focus on chewing-related frequencies.

  

3. **Feature Extraction:**

   - Extract relevant features from both audio and motion data, such as:

     - **Audio Features:** Amplitude, frequency components, zero-crossing rate, etc.

     - **Motion Features:** Acceleration peaks, frequency of jaw movements, etc.

  

4. **Chew Detection Algorithm:**

   - **Peak Detection for Motion Data:** Implement a histogram-based thresholding method to detect peaks in motion data representing chews.

   - **Audio Event Detection:** Use a similar peak detection or machine learning approach to identify chewing sounds.

  

5. **Data Fusion:**

   - Combine audio and motion features to improve detection accuracy. This can be done using techniques like feature concatenation or multi-modal neural networks.

  

6. **Machine Learning Model:**

   - **Training:** Train a classifier (e.g., ANN, SVM) using labeled data to distinguish between chewing and non-chewing periods.

   - **Validation:** Use cross-validation techniques to ensure the model's robustness.

  

7. **Chew Counting:**

   - Apply the trained model to classify data segments as chewing or non-chewing.

   - Count the number of detected chewing events in the classified segments.

  

### Detailed Steps

  

**1. Data Collection:**

- Use the AirPods' microphones to continuously record audio while eating.

- Simultaneously, collect motion data using the built-in accelerometer and gyroscope.

  

**2. Signal Preprocessing:**

- Apply a band-pass filter to the audio signal to isolate frequencies associated with chewing (typically between 0.94 to 2 Hz).

- For motion data, apply a similar band-pass filter to isolate jaw movement frequencies.

  

**3. Feature Extraction:**

- Extract time-domain and frequency-domain features from the audio signal, such as:

  - RMS amplitude

  - Spectral centroid

  - Zero-crossing rate

- For motion data, extract features such as:

  - Peak acceleration

  - Jaw movement frequency

  - Temporal patterns of movement

  

**4. Chew Detection Algorithm:**

- Implement a peak detection algorithm on the filtered motion data to identify potential chewing events.

- Use machine learning techniques (e.g., HMM, decision trees) to classify audio events as chewing or non-chewing.

  

**5. Data Fusion:**

- Combine features from both audio and motion data into a single feature vector for each time segment.

- Use techniques like feature concatenation or multi-modal neural networks to integrate data from both sources.

  

**6. Machine Learning Model:**

- Train an ANN or SVM classifier using the combined feature vectors. The input layer should correspond to the number of features, and the output layer should classify segments as chewing or non-chewing.

- Validate the model using cross-validation to ensure accuracy.

  

**7. Chew Counting:**

- Apply the trained classifier to new data segments to classify them as chewing or non-chewing.

- Count the number of detected chewing events within the classified chewing segments.

  

### Example Python Code

  

Here's a simplified example of how you might implement some of these steps in Python:

  

```python

import numpy as np

from scipy.signal import butter, lfilter

from sklearn.neural_network import MLPClassifier

from sklearn.model_selection import train_test_split, cross_val_score

  

# Butterworth band-pass filter

def butter_bandpass(lowcut, highcut, fs, order=5):

    nyq = 0.5 * fs

    low = lowcut / nyq

    high = highcut / nyq

    b, a = butter(order, [low, high], btype='band')

    return b, a

  

def bandpass_filter(data, lowcut, highcut, fs, order=5):

    b, a = butter_bandpass(lowcut, highcut, fs, order=order)

    y = lfilter(b, a, data)

    return y

  

# Feature extraction (example)

def extract_features(audio_data, motion_data):

    audio_features = np.array([np.mean(audio_data), np.std(audio_data)]) # Simplified

    motion_features = np.array([np.mean(motion_data), np.std(motion_data)]) # Simplified

    return np.concatenate((audio_features, motion_features))

  

# Data loading (placeholder)

audio_data = np.random.randn(1000) # Replace with actual audio data

motion_data = np.random.randn(1000) # Replace with actual motion data

  

# Filtering

filtered_audio = bandpass_filter(audio_data, 0.94, 2, 44100)

filtered_motion = bandpass_filter(motion_data, 0.94, 2, 100)

  

# Feature extraction

features = extract_features(filtered_audio, filtered_motion)

  

# Training data (placeholder)

X = np.array([features])

y = np.array([1]) # 1 for chewing, 0 for non-chewing

  

# Classifier

clf = MLPClassifier(hidden_layer_sizes=(5,), activation='tanh', solver='adam')

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

clf.fit(X_train, y_train)

  

# Cross-validation

scores = cross_val_score(clf, X, y, cv=5)

print(f"Accuracy: {np.mean(scores)}")

```

  

This is a simplified example to give you an idea of the process. For a complete implementation, you would need to handle data collection, preprocessing, feature extraction, and classifier training with more details and robustness.

  

### Detailed Preprocessing Steps for Chew Counting Using AirPods

  

**1. Signal Acquisition:**

   - **Audio Data:** Capture continuous audio recordings using AirPods' microphones.

   - **Motion Data:** Collect accelerometer and gyroscope data to track jaw movements.

  

**2. Signal Synchronization:**

   - Ensure both audio and motion data are time-synchronized to facilitate combined analysis.

  

**3. Noise Reduction:**

   - **Audio Data:** Apply noise reduction techniques to remove background noise. Methods include spectral subtraction, Wiener filtering, or more advanced noise reduction algorithms.

   - **Motion Data:** Remove artifacts caused by non-chewing activities (e.g., head movements) using preprocessing techniques like thresholding or median filtering.

  

**4. Band-pass Filtering:**

   - **Audio Filtering:** Apply a band-pass filter to isolate chewing frequencies (0.94 to 2 Hz). This can be achieved using a Butterworth or Chebyshev filter.

     ```python

     from scipy.signal import butter, lfilter

  

     def butter_bandpass(lowcut, highcut, fs, order=5):

         nyq = 0.5 * fs

         low = lowcut / nyq

         high = highcut / nyq

         b, a = butter(order, [low, high], btype='band')

         return b, a

  

     def bandpass_filter(data, lowcut, highcut, fs, order=5):

         b, a = butter_bandpass(lowcut, highcut, fs, order=order)

         y = lfilter(b, a, data)

         return y

  

     filtered_audio = bandpass_filter(audio_data, 0.94, 2, 44100)

     ```

   - **Motion Filtering:** Similarly, apply a band-pass filter to the accelerometer and gyroscope data to focus on relevant jaw movement frequencies.

     ```python

     filtered_motion = bandpass_filter(motion_data, 0.94, 2, 100)

     ```

  

**5. Signal Segmentation:**

   - Divide the preprocessed signals into fixed-length segments (e.g., 5-second epochs). This helps in managing data and analyzing short windows of activity.

     ```python

     def segment_signal(signal, segment_length, fs):

         num_samples = segment_length * fs

         segments = [signal[i:i + num_samples] for i in range(0, len(signal), num_samples)]

         return segments

  

     audio_segments = segment_signal(filtered_audio, 5, 44100)

     motion_segments = segment_signal(filtered_motion, 5, 100)

     ```

  

**6. Feature Extraction:**

   - Extract relevant features from each segment for both audio and motion data.

     - **Audio Features:** RMS amplitude, spectral centroid, zero-crossing rate, entropy, etc.

     - **Motion Features:** Mean acceleration, standard deviation, peak count, frequency components, etc.

     ```python

     def extract_features(segment):

         audio_features = np.array([np.mean(segment), np.std(segment), np.max(segment), np.min(segment)]) # Simplified

         motion_features = np.array([np.mean(segment), np.std(segment), np.max(segment), np.min(segment)]) # Simplified

         return np.concatenate((audio_features, motion_features))

  

     audio_features = [extract_features(seg) for seg in audio_segments]

     motion_features = [extract_features(seg) for seg in motion_segments]

     ```

  

**7. Data Fusion:**

   - Combine the features from audio and motion segments to create a comprehensive feature vector for each segment.

     ```python

     combined_features = [np.concatenate((a, m)) for a, m in zip(audio_features, motion_features)]

     ```

  

**8. Data Normalization:**

   - Normalize the combined feature vectors to ensure uniformity and improve the performance of the classification algorithm.

     ```python

     from sklearn.preprocessing import StandardScaler

  

     scaler = StandardScaler()

     normalized_features = scaler.fit_transform(combined_features)

     ```

  

**9. Classification:**

   - Use a machine learning classifier (e.g., ANN, SVM) to classify each segment as chewing or non-chewing based on the extracted features.

     ```python

     from sklearn.neural_network import MLPClassifier

  

     clf = MLPClassifier(hidden_layer_sizes=(5,), activation='tanh', solver='adam')

     clf.fit(normalized_features, labels)  # labels should be pre-defined

  

     # Predict new data

     predictions = clf.predict(new_normalized_features)

     ```

  

**10. Chew Counting:**

   - Apply the classifier to the data segments to identify chewing periods and count the number of detected chewing events.

  

By following these steps, you can replicate the chew counting algorithm using AirPods, leveraging both audio and motion data to accurately detect and quantify chewing behavior.