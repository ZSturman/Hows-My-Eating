# my_project/pipeline/overlay.py
import cv2
import pandas as pd

def overlay_text_on_video(input_video: str, csv_path: str, output_video: str):
    """
    Overlays text on each frame from CSV data (from step5).
    """
    cap = cv2.VideoCapture(input_video)
    df = pd.read_csv(csv_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx < len(df):
            row = df.iloc[frame_idx]
            text = f"Chew Count: {row['chew_count']}, Teeth: {row['teeth']}, Lips: {row['lips']}, Action: {row['action']}"
            cv2.putText(frame, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (255, 255, 255), 2, cv2.LINE_AA)

        out.write(frame)
        frame_idx += 1
        if frame_idx >= total_frames:
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()