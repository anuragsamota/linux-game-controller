import  { useState } from 'react';
import { BUTTON_TYPES, createNewButton } from '../utils/defaultConfigs';

const Toolbar = ({ 
  isEditMode, 
  onToggleEditMode, 
  onAddButton,
  onSaveConfig,
  isConnected,
  onDisconnect,
  onOpenConfigMenu,
  scale,
  onScaleChange,
  autoScale,
  onToggleAutoScale,
  isFullscreen,
  onToggleFullscreen,
  buttonScale,
  onButtonScaleChange,
  selectedButtonId,
  onDeleteSelected
}) => {
  const [showAddMenu, setShowAddMenu] = useState(false);

  const handleAddButton = (type) => {
    const newButton = createNewButton(type);
    onAddButton(newButton);
    setShowAddMenu(false);
  };

  return (
    <div className="flex items-center justify-between gap-1 px-2 py-1.5 bg-gray-900/90 backdrop-blur-sm border-b border-cyan-500/30 shadow-lg">
      <div className="flex items-center gap-1">
        <button
          onClick={onOpenConfigMenu}
          className="px-2 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-medium transition-all shadow-md"
        >
          ☰
        </button>
        
        {isConnected && (
          <button
            onClick={onDisconnect}
            className="px-2 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-medium transition-all shadow-md"
          >
            ✕
          </button>
        )}
      </div>
      
      <div className="flex items-center gap-1">
        {isEditMode && (
          <>
            <div className="relative">
              <button
                onClick={() => setShowAddMenu(!showAddMenu)}
                className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-all shadow-md"
              >
                +
              </button>
              
              {showAddMenu && (
                <div className="absolute top-full right-0 mt-1 bg-gray-900 border border-cyan-400/50 rounded shadow-lg z-50 min-w-40">
                  <div className="p-1 space-y-0.5">
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.ACTION)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300"
                    >
                      Action Button
                    </button>
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.DPAD)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300"
                    >
                      D-Pad
                    </button>
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.SHOULDER)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300"
                    >
                      Shoulder Button
                    </button>
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.TRIGGER)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300"
                    >
                      Trigger
                    </button>
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.SPECIAL)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300"
                    >
                      Special Button
                    </button>
                    <hr className="border-cyan-400/20 my-0.5" />
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.JOYSTICK)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300 font-medium"
                    >
                      ◯ Joystick
                    </button>
                    <button
                      onClick={() => handleAddButton(BUTTON_TYPES.TOUCHPAD)}
                      className="w-full text-left px-2 py-1 hover:bg-cyan-500/20 rounded text-xs text-cyan-300 font-medium"
                    >
                      ⬜ Touchpad
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {selectedButtonId && (
              <button
                onClick={onDeleteSelected}
                className="px-2 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-medium transition-all shadow-md"
                title="Delete selected control"
              >
                🗑️
              </button>
            )}
            
            <button
              onClick={onSaveConfig}
              className="px-2 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-medium transition-all shadow-md"
            >
              💾
            </button>
            
            <div className="flex items-center gap-0.5 px-1.5 py-1 bg-gray-800 rounded border border-cyan-500/30">
              <span className="text-xs text-cyan-300 font-medium">Btn:</span>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={buttonScale}
                onChange={(e) => onButtonScaleChange(parseFloat(e.target.value))}
                className="w-12 h-1"
              />
              <span className="text-xs text-cyan-300 w-6 text-center">{buttonScale.toFixed(1)}x</span>
            </div>
          </>
        )}
        
        <div className="flex items-center gap-0.5 px-1.5 py-1 bg-gray-800 rounded border border-cyan-500/30">
          <button
            onClick={onToggleAutoScale}
            className={`text-xs px-1 py-0.5 rounded transition-all font-medium ${
              autoScale 
                ? 'bg-cyan-600 text-white' 
                : 'bg-gray-700 text-gray-300'
            }`}
            title="Toggle automatic responsive scaling"
          >
            A
          </button>
          <input
            type="range"
            min="0.5"
            max="1.5"
            step="0.1"
            value={scale}
            onChange={(e) => onScaleChange(parseFloat(e.target.value))}
            disabled={autoScale}
            className={`w-12 h-1 ${autoScale ? 'opacity-50 cursor-not-allowed' : ''}`}
          />
          <span className="text-xs text-cyan-300 w-6 text-center">{scale.toFixed(1)}x</span>
        </div>

        <button
          onClick={onToggleFullscreen}
          className="px-1.5 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded transition-all border border-cyan-500/30"
          title={isFullscreen ? 'Exit Fullscreen (F11)' : 'Enter Fullscreen (F11)'}
        >
          {isFullscreen ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-5v4m0-4h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>
        
        <button
          onClick={onToggleEditMode}
          className={`px-2 py-1 rounded text-xs font-medium transition-all ${
            isEditMode 
              ? 'bg-yellow-500 text-black hover:bg-yellow-600 shadow-md' 
              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-md'
          }`}
        >
          {isEditMode ? '✓' : '✏️'}
        </button>
      </div>
    </div>
  );
};

export default Toolbar;
