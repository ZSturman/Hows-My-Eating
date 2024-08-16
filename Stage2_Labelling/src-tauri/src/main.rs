// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command

#[tauri::command]
fn load_video_path(file_path: String) -> String {
    file_path
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![load_video_path])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}