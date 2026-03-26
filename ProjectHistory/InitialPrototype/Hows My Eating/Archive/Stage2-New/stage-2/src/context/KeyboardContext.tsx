import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

// Define types for the state and context
interface KeyboardContextType {
  pressedKeys: Set<string>;
}

// Create the context
const KeyboardContext = createContext<KeyboardContextType | undefined>(undefined);

// Provider component
export const KeyboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set());
  const pressedKeysRef = useRef(pressedKeys);
  const hotkeysMap: { [key: string]: () => void } = {};



  // Handle keydown and keyup events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (!pressedKeysRef.current.has(key)) {
        const newPressedKeys = new Set(pressedKeysRef.current);
        newPressedKeys.add(key);
        setPressedKeys(newPressedKeys);
        pressedKeysRef.current = newPressedKeys;
        console.log(`Key down: ${key}`);
      }

      // Check if any registered hotkey matches
      const pressedKeysString = Array.from(pressedKeysRef.current).sort().join('+');
      console.log(`Pressed keys: ${pressedKeysString}`); // Log the current combination of pressed keys

      if (hotkeysMap[pressedKeysString]) {
        console.log(`Hotkey triggered: ${pressedKeysString}`);
        hotkeysMap[pressedKeysString]();
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (pressedKeysRef.current.has(key)) {
        const newPressedKeys = new Set(pressedKeysRef.current);
        newPressedKeys.delete(key);
        setPressedKeys(newPressedKeys);
        pressedKeysRef.current = newPressedKeys;
        console.log(`Key up: ${key}`);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    // Cleanup event listeners on component unmount or when effect re-runs
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []); // Empty dependency array to ensure this effect runs only once

  return (
    <KeyboardContext.Provider value={{ pressedKeys }}>
      {children}
    </KeyboardContext.Provider>
  );
};

// Custom hook to use the KeyboardContext
export const useKeyboard = (): KeyboardContextType => {
  const context = useContext(KeyboardContext);
  if (!context) {
    throw new Error('useKeyboard must be used within a KeyboardProvider');
  }
  return context;
};