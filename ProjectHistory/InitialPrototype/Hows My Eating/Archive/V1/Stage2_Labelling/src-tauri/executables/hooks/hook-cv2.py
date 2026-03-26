from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('cv2')
datas = collect_data_files('cv2')