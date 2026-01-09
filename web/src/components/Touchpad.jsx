import React, { useState, useRef, useEffect } from 'react';

const Touchpad = ({ 
  touchpad, 
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
  const [touchPos, setTouchPos] = useState({ x: 0, y: 0 });
  const touchpadRef = useRef(null);
  const dragStartRef = useRef({ x: 0, y: 0, buttonX: 0, buttonY: 0 });
  const resizeStartRef = useRef({ x: 0, y: 0, width: 0, height: 0 });

  const handlePointerDown = (e) => {
    if (isEditMode) {
      e.preventDefault();
      e.stopPropagation();
      onSelect(touchpad.id);
      
      if (e.target.classList.contains('resize-handle')) {
        setIsResizing(true);
        resizeStartRef.current = {
          x: e.clientX,
          y: e.clientY,
          width: touchpad.width,
          height: touchpad.height,
        };
      } else {
        setIsDragging(true);
        dragStartRef.current = {
          x: e.clientX,
          y: e.clientY,
          buttonX: touchpad.x,
          buttonY: touchpad.y,
        };
      }
    } else {
      e.preventDefault();
      e.stopPropagation();
      setIsPressed(true);
      handleTouchMove(e);
    }
  };

  const handlePointerMove = (e) => {
    if (isEditMode && isDragging && touchpadRef.current) {
      const container = touchpadRef.current.parentElement;
      const rect = container.getBoundingClientRect();
      
      const deltaX = ((e.clientX - dragStartRef.current.x) / rect.width) * 100;
      const deltaY = ((e.clientY - dragStartRef.current.y) / rect.height) * 100;
      
      const newX = Math.max(0, Math.min(95, dragStartRef.current.buttonX + deltaX));
      const newY = Math.max(0, Math.min(95, dragStartRef.current.buttonY + deltaY));
      
      onUpdate?.({ ...touchpad, x: newX, y: newY });
    } else if (isEditMode && isResizing && touchpadRef.current) {
      const container = touchpadRef.current.parentElement;
      const rect = container.getBoundingClientRect();
      
      const deltaX = ((e.clientX - resizeStartRef.current.x) / rect.width) * 100;
      const deltaY = ((e.clientY - resizeStartRef.current.y) / rect.height) * 100;
      
      const newWidth = Math.max(5, Math.min(30, resizeStartRef.current.width + deltaX));
      const newHeight = Math.max(5, Math.min(30, resizeStartRef.current.height + deltaY));
      
      onUpdate?.({ ...touchpad, width: newWidth, height: newHeight });
    } else if (!isEditMode && isPressed) {
      handleTouchMove(e);
    }
  };

  const handlePointerUp = (e) => {
    if (isEditMode) {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      setIsResizing(false);
    } else {
      setIsPressed(false);
      setTouchPos({ x: 0, y: 0 });
      onRelease?.(touchpad.id, 0, 0);
    }
  };

  const handleTouchMove = (e) => {
    if (!touchpadRef.current) return;
    
    const rect = touchpadRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = e.clientX - centerX;
    const deltaY = e.clientY - centerY;
    
    // Normalize to -1 to 1 range
    const maxX = rect.width / 2;
    const maxY = rect.height / 2;
    
    let normalizedX = deltaX / maxX;
    let normalizedY = deltaY / maxY;
    
    normalizedX = Math.max(-1, Math.min(1, normalizedX));
    normalizedY = Math.max(-1, Math.min(1, normalizedY));
    
    setTouchPos({ x: normalizedX, y: normalizedY });
    onPress?.(touchpad.id, normalizedX, normalizedY);
  };

  // Handle Delete key press when touchpad is selected
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isEditMode && isSelected && (e.key === 'Delete' || e.key === 'Backspace')) {
        e.preventDefault();
        onDelete?.(touchpad.id);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isEditMode, isSelected, touchpad.id, onDelete]);

  const touchpadStyle = {
    left: `${touchpad.x}%`,
    top: `${touchpad.y}%`,
    width: `${touchpad.width}%`,
    paddingBottom: `${touchpad.height}%`,
    backgroundColor: touchpad.color,
    opacity: isEditMode ? 0.8 : 0.85,
    transform: `scale(${scale * (touchpad.scale ?? 1) * buttonScale})`,
    aspectRatio: `${touchpad.width} / ${touchpad.height}`,
    filter: isPressed && !isEditMode ? 'brightness(1.3)' : 'brightness(1)',
    transition: isDragging || isResizing ? 'none' : 'filter 80ms ease-out',
  };

  const touchIndicatorX = touchPos.x * 40;
  const touchIndicatorY = touchPos.y * 40;

  return (
    <div
      ref={touchpadRef}
      className={`absolute rounded-lg cursor-pointer overflow-hidden shadow-md
        ${isEditMode ? 'border-2 border-dashed border-white/50' : 'border border-white/20'}
        ${isSelected ? 'border-cyan-400 ring-4 ring-cyan-400/50 shadow-lg shadow-cyan-400/30' : ''}
        ${isDragging || isResizing ? 'z-50 opacity-100' : ''}
      `}
      style={touchpadStyle}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <div className="absolute inset-0 flex items-center justify-center drop-shadow-lg">
        <div className="relative w-full h-full">
          {/* Touch indicator dot */}
          <div 
            className="absolute w-1/3 h-1/3 bg-white/50 rounded-full border-2 border-white/70 shadow-lg pointer-events-none"
            style={{
              left: '50%',
              top: '50%',
              transform: `translate(calc(-50% + ${touchIndicatorX}%), calc(-50% + ${touchIndicatorY}%))`,
              transition: 'none'
            }}
          />
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white drop-shadow-md">
            {touchpad.label}
          </span>
        </div>
      </div>
      
      {/* Show delete button hint in edit mode even when not selected */}
      {isEditMode && !isSelected && (
        <div className="absolute -top-3 -right-3 bg-red-500/70 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs z-10 pointer-events-none">
          ×
        </div>
      )}
      
      {isEditMode && isSelected && (
        <>
          <div className="resize-handle absolute bottom-0 right-0 w-4 h-4 bg-cyan-400 rounded-tl cursor-nwse-resize z-10" />
          <div className="absolute -top-8 left-0 right-0 bg-gray-900 rounded px-2 py-1 text-xs text-white whitespace-nowrap flex items-center gap-1 z-20 border border-cyan-400/50">
            <span className="text-cyan-300">Scale:</span>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={touchpad.scale ?? 1}
              onChange={(e) => onUpdate?.({ ...touchpad, scale: parseFloat(e.target.value) })}
              className="w-16 h-1"
              onClick={(e) => e.stopPropagation()}
              onPointerDown={(e) => e.stopPropagation()}
            />
            <span className="w-6 text-right text-cyan-300">{(touchpad.scale ?? 1).toFixed(1)}x</span>
          </div>
          <div className="absolute -top-12 right-0 bg-gray-900 rounded px-2 py-1 text-xs text-gray-300 border border-cyan-400/50 whitespace-nowrap z-20">
            Press Delete to remove
          </div>
          <button
            className="absolute -top-6 -right-6 bg-red-500 text-white rounded-full w-7 h-7 flex items-center justify-center text-sm hover:bg-red-600 z-10 shadow-lg font-bold transition-all active:scale-90"
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.(touchpad.id);
            }}
            title="Delete this touchpad (Delete key)"
          >
            ×
          </button>
        </>
      )}
    </div>
  );
};

export default Touchpad;
