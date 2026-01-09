import React, { useState, useEffect, useRef } from 'react';
import ConnectionScreen from './components/ConnectionScreen';
import Controller from './components/Controller';
import Toolbar from './components/Toolbar';
import ConfigMenu from './components/ConfigMenu';
import WebSocketManager from './utils/WebSocketManager';
import { storage } from './utils/storage';
import { DEFAULT_CONFIGS } from './utils/defaultConfigs';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const wsRef = useRef(null);
  const [configs, setConfigs] = useState([]);
  const [activeConfigId, setActiveConfigId] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showConfigMenu, setShowConfigMenu] = useState(false);
  const [scale, setScale] = useState(1);
  const [autoScale, setAutoScale] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [buttonScale, setButtonScale] = useState(1);
  const [selectedButtonId, setSelectedButtonId] = useState(null);

  useEffect(() => {
    const updateScale = () => {
      if (autoScale) {
        const width = window.innerWidth;
        const height = window.innerHeight;
        // Scale based on smaller dimension for landscape optimization
        const minDimension = Math.min(width, height);
        let newScale = 1;
        
        if (minDimension < 600) {
          newScale = 0.7;
        } else if (minDimension < 800) {
          newScale = 0.85;
        } else if (minDimension > 1400) {
          newScale = 1.2;
        }
        
        // Additional scaling for very wide screens in landscape
        if (width / height > 2) {
          newScale *= 1.1;
        }
        
        setScale(newScale);
      }
    };
    
    updateScale();
    window.addEventListener('resize', updateScale);
    window.addEventListener('orientationchange', updateScale);
    
    return () => {
      window.removeEventListener('resize', updateScale);
      window.removeEventListener('orientationchange', updateScale);
    };
  }, [autoScale]);

  // Fullscreen management
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    const handleKeyPress = (e) => {
      if (e.key === 'F11') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen error:', error);
    }
  };

  const buttonStateRef = useRef({});

  useEffect(() => {
    const savedConfigs = storage.getConfigs();
    if (savedConfigs.length > 0) {
      setConfigs(savedConfigs);
      const activeId = storage.getActiveConfigId() || savedConfigs[0].id;
      setActiveConfigId(activeId);
    } else {
      const defaultConfig = { ...DEFAULT_CONFIGS[0], id: `config-${Date.now()}` };
      setConfigs([defaultConfig]);
      setActiveConfigId(defaultConfig.id);
      storage.saveConfigs([defaultConfig]);
      storage.setActiveConfigId(defaultConfig.id);
    }
  }, []);

  const activeConfig = configs.find(c => c.id === activeConfigId);

  const handleConnect = async (host, port, deviceName) => {
    setIsConnecting(true);
    try {
      if (!wsRef.current) wsRef.current = new WebSocketManager();
      await wsRef.current.connect(host, port, deviceName);
      setIsConnected(true);
      setIsConnecting(false);
    } catch (error) {
      alert(`Failed to connect: ${error.message}`);
      setIsConnecting(false);
    }
  };

  const handleDisconnect = () => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    setIsConnected(false);
    buttonStateRef.current = {};
  };

  // Map button IDs to API button names (matching server implementation)
  const getButtonName = (buttonId) => {
    const buttonNameMap = {
      'a': 'a', 'b': 'b', 'x': 'x', 'y': 'y',
      'up': 'dpad_up', 'down': 'dpad_down', 'left': 'dpad_left', 'right': 'dpad_right',
      'dpad_up': 'dpad_up', 'dpad_down': 'dpad_down', 'dpad_left': 'dpad_left', 'dpad_right': 'dpad_right',
      'lb': 'l1', 'rb': 'r1', 'lt': 'l2_click', 'rt': 'r2_click',
      'l1': 'l1', 'r1': 'r1', 'l2': 'l2_click', 'r2': 'r2_click',
      'start': 'start', 'select': 'back', 'back': 'back',
      'ls': 'l3', 'rs': 'r3', 'l3': 'l3', 'r3': 'r3',
    };
    return buttonNameMap[buttonId] || buttonId;
  };

  const handleButtonPress = (buttonId, type, data) => {
    if (!wsRef.current || !isConnected) return;
    if (type === 'joystick') {
      const axisPrefix = data.axis === 'left' ? 'l' : 'r';
      wsRef.current.sendAxis(`${axisPrefix}x`, data.x);
      wsRef.current.sendAxis(`${axisPrefix}y`, data.y);
      buttonStateRef.current[buttonId] = { type: 'joystick', x: data.x, y: data.y };
    } else if (type === 'touchpad') {
      wsRef.current.sendAxis('px', data.x);
      wsRef.current.sendAxis('py', data.y);
      buttonStateRef.current[buttonId] = { type: 'touchpad', x: data.x, y: data.y };
    } else {
      wsRef.current.sendButton(getButtonName(buttonId), true);
      buttonStateRef.current[buttonId] = { type: 'button', pressed: true };
    }
  };

  const handleButtonRelease = (buttonId, type, data) => {
    if (!wsRef.current || !isConnected) return;
    if (type === 'joystick') {
      const button = activeConfig?.buttons.find(b => b.id === buttonId);
      if (button) {
        const axisPrefix = button.axis === 'left' ? 'l' : 'r';
        wsRef.current.sendAxis(`${axisPrefix}x`, 0);
        wsRef.current.sendAxis(`${axisPrefix}y`, 0);
      }
    } else if (type === 'touchpad') {
      wsRef.current.sendAxis('px', 0);
      wsRef.current.sendAxis('py', 0);
    } else {
      wsRef.current.sendButton(getButtonName(buttonId), false);
    }
    delete buttonStateRef.current[buttonId];
  };

  const handleSelectConfig = (configId) => {
    setActiveConfigId(configId);
    storage.setActiveConfigId(configId);
    setShowConfigMenu(false);
  };

  const handleCreateConfig = (newConfig) => {
    const updatedConfigs = [...configs, newConfig];
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
    setActiveConfigId(newConfig.id);
    storage.setActiveConfigId(newConfig.id);
  };

  const handleDuplicateConfig = (configId) => {
    const configToDupe = configs.find(c => c.id === configId);
    if (configToDupe) {
      const duplicated = {
        ...configToDupe,
        id: `config-${Date.now()}`,
        name: `${configToDupe.name} (Copy)`,
        buttons: configToDupe.buttons.map(btn => ({ ...btn, id: `btn-${Date.now()}-${Math.random()}` }))
      };
      const updatedConfigs = [...configs, duplicated];
      setConfigs(updatedConfigs);
      storage.saveConfigs(updatedConfigs);
    }
  };

  const handleDeleteConfig = (configId) => {
    const updatedConfigs = configs.filter(c => c.id !== configId);
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
    if (activeConfigId === configId && updatedConfigs.length > 0) {
      setActiveConfigId(updatedConfigs[0].id);
      storage.setActiveConfigId(updatedConfigs[0].id);
    }
  };

  const handleRenameConfig = (configId, newName) => {
    const updatedConfigs = configs.map(c => c.id === configId ? { ...c, name: newName } : c);
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
  };

  const handleImportConfig = (config) => {
    const updatedConfigs = [...configs, config];
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
    setActiveConfigId(config.id);
    storage.setActiveConfigId(config.id);
    setShowConfigMenu(false);
  };

  const handleAddButton = (newButton) => {
    if (!activeConfig) return;
    const updatedConfig = { ...activeConfig, buttons: [...activeConfig.buttons, newButton] };
    const updatedConfigs = configs.map(c => c.id === activeConfigId ? updatedConfig : c);
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
  };

  const handleUpdateButton = (updatedButton) => {
    if (!activeConfig) return;
    const updatedConfig = { ...activeConfig, buttons: activeConfig.buttons.map(b => b.id === updatedButton.id ? updatedButton : b) };
    const updatedConfigs = configs.map(c => c.id === activeConfigId ? updatedConfig : c);
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
  };

  const handleDeleteButton = (buttonId) => {
    if (!activeConfig) return;
    const updatedConfig = { ...activeConfig, buttons: activeConfig.buttons.filter(b => b.id !== buttonId) };
    const updatedConfigs = configs.map(c => c.id === activeConfigId ? updatedConfig : c);
    setConfigs(updatedConfigs);
    storage.saveConfigs(updatedConfigs);
  };

  const handleSaveConfig = () => {
    storage.saveConfigs(configs);
    setIsEditMode(false);
    alert('Configuration saved!');
  };

  if (!isConnected) {
    return <ConnectionScreen onConnect={handleConnect} isConnecting={isConnecting} />;
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-gamepad-background">
      <Toolbar
        isEditMode={isEditMode}
        onToggleEditMode={() => setIsEditMode(!isEditMode)}
        onAddButton={handleAddButton}
        onSaveConfig={handleSaveConfig}
        isConnected={isConnected}
        onDisconnect={handleDisconnect}
        onOpenConfigMenu={() => setShowConfigMenu(true)}
        scale={scale}
        onScaleChange={(newScale) => {
          setScale(newScale);
          setAutoScale(false);
        }}
        autoScale={autoScale}
        onToggleAutoScale={() => setAutoScale(!autoScale)}
        isFullscreen={isFullscreen}
        onToggleFullscreen={toggleFullscreen}
        buttonScale={buttonScale}
        onButtonScaleChange={setButtonScale}
        selectedButtonId={selectedButtonId}
        onDeleteSelected={() => {
          if (selectedButtonId) {
            handleDeleteButton(selectedButtonId);
            setSelectedButtonId(null);
          }
        }}
      />
      <div className="flex-1 p-4 overflow-hidden">
        {activeConfig ? (
          <Controller
            config={activeConfig}
            isEditMode={isEditMode}
            onButtonPress={handleButtonPress}
            onButtonRelease={handleButtonRelease}
            onUpdateButton={handleUpdateButton}
            onDeleteButton={handleDeleteButton}
            scale={scale}
            buttonScale={buttonScale}
            onSelectedButtonChange={setSelectedButtonId}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-xl">
            No controller configuration loaded
          </div>
        )}
      </div>
      {showConfigMenu && (
        <ConfigMenu
          configs={configs}
          activeConfigId={activeConfigId}
          onSelectConfig={handleSelectConfig}
          onCreateConfig={handleCreateConfig}
          onDuplicateConfig={handleDuplicateConfig}
          onDeleteConfig={handleDeleteConfig}
          onRenameConfig={handleRenameConfig}
          onClose={() => setShowConfigMenu(false)}
          onImportConfig={handleImportConfig}
        />
      )}
    </div>
  );
}

export default App;
