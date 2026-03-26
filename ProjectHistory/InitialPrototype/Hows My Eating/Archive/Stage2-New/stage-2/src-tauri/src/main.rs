#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[tauri::command]
fn calculate_frame(current_time: f64, playback_speed: f64, fps: u32) -> u32 {
    let frame_number = (current_time * fps as f64 * playback_speed).floor() as u32;
    frame_number
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![calculate_frame])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}