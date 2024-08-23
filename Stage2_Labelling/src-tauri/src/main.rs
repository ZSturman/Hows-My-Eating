// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use tauri::{CustomMenuItem, Menu, Submenu};

#[tauri::command]
fn load_video_path(file_path: String) -> String {
    file_path
}

fn main() {
  // Create custom menu items
  let import = CustomMenuItem::new("import".to_string(), "Import Files");
  let quit = CustomMenuItem::new("quit".to_string(), "Quit");

  // File menu
  let file_menu = Submenu::new(
    "File",
    Menu::new().add_item(import).add_item(quit)
  );

  // Edit menu
  let undo = CustomMenuItem::new("undo".to_string(), "Undo");
  let redo = CustomMenuItem::new("redo".to_string(), "Redo");
  let cut = CustomMenuItem::new("cut".to_string(), "Cut");
  let copy = CustomMenuItem::new("copy".to_string(), "Copy");
  let paste = CustomMenuItem::new("paste".to_string(), "Paste");
  let edit_menu = Submenu::new(
    "Edit",
    Menu::new()
      .add_item(undo)
      .add_item(redo)
      .add_item(cut)
      .add_item(copy)
      .add_item(paste)
  );

  // Window menu
  let minimize = CustomMenuItem::new("minimize".to_string(), "Minimize");
  let zoom = CustomMenuItem::new("zoom".to_string(), "Zoom");
  let window_menu = Submenu::new(
    "Window",
    Menu::new().add_item(minimize).add_item(zoom)
  );

  // Help menu
  let about = CustomMenuItem::new("about".to_string(), "About");
  let help_menu = Submenu::new(
    "Help",
    Menu::new().add_item(about)
  );

  // Create the main menu and add the submenus
  let menu = Menu::new()
    .add_submenu(file_menu)
    .add_submenu(edit_menu)
    .add_submenu(window_menu)
    .add_submenu(help_menu);

  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![load_video_path])
    .menu(menu)
    .on_menu_event(|event| {
      match event.menu_item_id() {
        "import" => {
          // Trigger your import function here
          println!("Import function triggered");
        }
        "quit" => {
          std::process::exit(0);
        }
        "undo" => {
          println!("Undo action triggered");
        }
        "redo" => {
          println!("Redo action triggered");
        }
        "cut" => {
          println!("Cut action triggered");
        }
        "copy" => {
          println!("Copy action triggered");
        }
        "paste" => {
          println!("Paste action triggered");
        }
        "minimize" => {
          // Minimize window action
          event.window().minimize().unwrap();
        }
        "zoom" => {
          // Zoom window action (macOS specific)
          event.window().maximize().unwrap();
        }
        "about" => {
          println!("About action triggered");
        }
        _ => {}
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}