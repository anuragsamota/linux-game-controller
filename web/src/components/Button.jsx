import React, { useState, useRef, useEffect } from 'react';

const Button = ({ 
  button, 
  isEditMode, 
  isSelected, 
  onPress, 
  onRelease, 
  onSelect, 
  onUpdate,
  onDelete,
  scale = 1,
  buttonScale = 1
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [joystickPos, setJoystickPos] = useState({ x: 0, y: 0 });
  const buttonRef = useRef(null);
  const dragStartRef = useRef({ x: 0, y: 0, buttonX: 0, buttonY: 0 });
  const resizeStartRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

  const handlePointerDown = (e) => {
    if (isEditMode) {
      e.preventDefault();
      e.stopPropagation();
      onSelect(button.id);
      
      // Only allow dragging to move position, no resizing
      setIsDragging(true);
      dragStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        buttonX: button.x,
        buttonY: button.y,
      };
    } else {
      e.preventDefault();
      e.stopPropagation();
      setIsPressed(true);
      
      if (button.isJoystick) {
        handleJoystickMove(e);
      } else {
        onPress?.(button.id);
      }
    }
  };

  const handlePointerMove = (e) => {
    if (isEditMode && isDragging && buttonRef.current) {
      const container = buttonRef.current.parentElement;
      const rect = container.getBoundingClientRect();
      
      const deltaX = ((e.clientX - dragStartRef.current.x) / rect.width) * 100;
      const deltaY = ((e.clientY - dragStartRef.current.y) / rect.height) * 100;
      
      const newX = Math.max(0, Math.min(95, dragStartRef.current.buttonX + deltaX));
      const newY = Math.max(0, Math.min(95, dragStartRef.current.buttonY + deltaY));
      
      onUpdate?.({ ...button, x: newX, y: newY });
    } else if (!isEditMode && isPressed && button.isJoystick) {
      handleJoystickMove(e);
    }
  };

  const handlePointerUp = (e) => {
    if (isEditMode) {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
    } else {
      setIsPressed(false);
      
      if (button.isJoystick) {
        setJoystickPos({ x: 0, y: 0 });
        onRelease?.(button.id, 0, 0);
      } else {
        onRelease?.(button.id);
      }
    }
  };

  const handleJoystickMove = (e) => {
    if (!buttonRef.current) return;
    
    const rect = buttonRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = e.clientX - centerX;
    const deltaY = e.clientY - centerY;
    
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    const maxDistance = rect.width / 2;
    
    let normalizedX = deltaX / maxDistance;
    let normalizedY = deltaY / maxDistance;
    
    // Clamp to circle
    if (distance > maxDistance) {
      const ratio = maxDistance / distance;
      normalizedX *= ratio;
      normalizedY *= ratio;
    }
    
    normalizedX = Math.max(-1, Math.min(1, normalizedX));
    normalizedY = Math.max(-1, Math.min(1, normalizedY));
    
    // Apply deadzone
    const deadzone = 0.1;
    if (Math.abs(normalizedX) < deadzone) normalizedX = 0;
    if (Math.abs(normalizedY) < deadzone) normalizedY = 0;
    
    setJoystickPos({ x: normalizedX, y: normalizedY });
    onPress?.(button.id, normalizedX, normalizedY);
  };

  useEffect(() => {
    if (isDragging || isResizing) {
      const handleMove = (e) => handlePointerMove(e);
      const handleUp = (e) => handlePointerUp(e);
      
      window.addEventListener('pointermove', handleMove);
      window.addEventListener('pointerup', handleUp);
      
      return () => {
        window.removeEventListener('pointermove', handleMove);
        window.removeEventListener('pointerup', handleUp);
      };
    }
  }, [isDragging, isResizing]);

  // Handle Delete key press when button is selected
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isEditMode && isSelected && (e.key === 'Delete' || e.key === 'Backspace')) {
        e.preventDefault();
        onDelete?.(button.id);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isEditMode, isSelected, button.id, onDelete]);

  const buttonStyle = {
    left: `${button.x}%`,
    top: `${button.y}%`,
    width: `${button.width}%`,
    paddingBottom: `${button.height}%`,
    backgroundColor: button.color,
    opacity: isEditMode ? 0.8 : 0.85,
    transform: `scale(${scale * (button.scale ?? 1) * buttonScale})`,
    aspectRatio: `${button.width} / ${button.height}`,
    filter: isPressed && !isEditMode ? 'brightness(1.3)' : 'brightness(1)',
    transition: isDragging ? 'none' : 'filter 80ms ease-out',
  };

  const joystickIndicatorStyle = button.isJoystick ? {
    transform: `translate(${joystickPos.x * 80}%, ${joystickPos.y * 80}%)`,
  } : {};

  return (
    <div
      ref={buttonRef}
      className={`absolute font-bold cursor-pointer overflow-hidden shadow-md
        ${button.type === 'action' ? 'rounded-full' : 'rounded-lg'}
        ${isEditMode ? 'border-2 border-dashed border-white/50' : 'border border-white/20'}
        ${isSelected ? 'border-cyan-400 ring-4 ring-cyan-400/50 shadow-lg shadow-cyan-400/30' : ''}
        ${isDragging ? 'z-50 opacity-100' : ''}
      `}
      style={buttonStyle}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <div className="absolute inset-0 flex items-center justify-center drop-shadow-lg">
        {button.isJoystick ? (
          <div className="relative w-full h-full flex items-center justify-center">
            <div 
              className="absolute w-2/3 h-2/3 bg-white/50 rounded-full border-2 border-white/70 shadow-lg"
              style={{...joystickIndicatorStyle, transition: 'none'}}
            />
            <span className="text-xs font-bold text-white z-10 drop-shadow-md">{button.label}</span>
          </div>
        ) : (
          <span className="text-sm font-bold text-white drop-shadow-md">{button.label}</span>
        )}
      </div>
      
      {/* Show delete button hint in edit mode even when not selected */}
      {isEditMode && !isSelected && (
        <div className="absolute -top-3 -right-3 bg-red-500/70 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs z-10 pointer-events-none">
          ×
        </div>
      )}
      
      {isEditMode && isSelected && (
        <>
          <div className="absolute -top-28 left-0 bg-gray-900/95 backdrop-blur-md rounded-lg p-3 shadow-xl border border-cyan-400/50 z-50 min-w-[220px]">
            <div className="space-y-2">
              <div>
                <label className="text-xs text-white/70 block mb-1">Width: {button.width}px</label>
                <input
                  type="range"
                  min="40"
                  max="200"
                  value={button.width}
                  onChange={(e) => {
                    const newWidth = parseInt(e.target.value);
                    onUpdate({ ...button, width: newWidth });
                  }}
                  onClick={(e) => e.stopPropagation()}
                  onPointerDown={(e) => e.stopPropagation()}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-xs text-white/70 block mb-1">Height: {button.height}px</label>
                <input
                  type="range"
                  min="40"
                  max="200"
                  value={button.height}
                  onChange={(e) => {
                    const newHeight = parseInt(e.target.value);
                    onUpdate({ ...button, height: newHeight });
                  }}
                  onClick={(e) => e.stopPropagation()}
                  onPointerDown={(e) => e.stopPropagation()}
                  className="w-full"
                />
              </div>
            </div>
          </div>
          <div className="absolute -top-8 left-0 right-0 bg-gray-900 rounded px-2 py-1 text-xs text-white whitespace-nowrap flex items-center gap-1 z-20 border border-cyan-400/50">
            <span className="text-cyan-300">Scale:</span>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={button.scale ?? 1}
              onChange={(e) => onUpdate?.({ ...button, scale: parseFloat(e.target.value) })}
              className="w-16 h-1"
              onClick={(e) => e.stopPropagation()}
              onPointerDown={(e) => e.stopPropagation()}
            />
            <span className="w-6 text-right text-cyan-300">{(button.scale ?? 1).toFixed(1)}x</span>
          </div>
          <div className="absolute -top-12 right-0 bg-gray-900 rounded px-2 py-1 text-xs text-gray-300 border border-cyan-400/50 whitespace-nowrap z-20">
            Press Delete to remove
          </div>
          <button
            className="absolute -top-6 -right-6 bg-red-500 text-white rounded-full w-7 h-7 flex items-center justify-center text-sm hover:bg-red-600 z-10 shadow-lg font-bold transition-all active:scale-90"
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(button.id);
            }}
            title="Delete this button (Delete key)"
          >
            ×
          </button>
        </>
      )}
    </div>
  );
};

export default Button;
