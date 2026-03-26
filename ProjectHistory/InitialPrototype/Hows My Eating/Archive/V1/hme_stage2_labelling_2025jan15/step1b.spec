# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/step1b.py'],
    pathex=['src', 'venv/lib/python3.12/site-packages'],
    binaries=[],
    datas=[('src/models/shape_predictor_68_face_landmarks.dat', 'src/models'), ('/Users/zacharysturman/Desktop/hme_stage2_labelling_2025jan15/venv/lib/python3.12/site-packages/mediapipe/modules/hand_landmark/hand_landmark_full.tflite', 'mediapipe/modules/hand_landmark'), ('/Users/zacharysturman/Desktop/hme_stage2_labelling_2025jan15/venv/lib/python3.12/site-packages/mediapipe/modules/hand_landmark/hand_landmark_tracking_cpu.binarypb', 'mediapipe/modules/hand_landmark'), ('/Users/zacharysturman/Desktop/hme_stage2_labelling_2025jan15/venv/lib/python3.12/site-packages/mediapipe/modules/hand_landmark/handedness.txt', 'mediapipe/modules/hand_landmark'), ('/Users/zacharysturman/Desktop/hme_stage2_labelling_2025jan15/venv/lib/python3.12/site-packages/mediapipe/modules/palm_detection/palm_detection_full.tflite', 'mediapipe/modules/palm_detection')],
    hiddenimports=['cv2', 'pipeline', 'numpy', 'mediapipe'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='step1b',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
