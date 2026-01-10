import React, { useState, useRef, useEffect } from 'react';
import Button from './Button';
import Touchpad from './Touchpad';

const Controller = ({ 
  config, 
  isEditMode, 
  onButtonPress, 
  onButtonRelease,
  onTouchpadTap,
  onUpdateButton,
  onDeleteButton,
  scale = 1,
  buttonScale = 1,
  onSelectedButtonChange
}) => {
  const [selectedButtonId, setSelectedButtonId] = useState(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef(null);

  // Notify parent when selection changes
  useEffect(() => {
    onSelectedButtonChange?.(selectedButtonId);
  }, [selectedButtonId, onSelectedButtonChange]);

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setContainerSize({ width: rect.width, height: rect.height });
      }
    };
    
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const handleButtonPress = (buttonId, x, y) => {
    const button = config.buttons.find(b => b.id === buttonId);
    if (button?.isJoystick) {
      onButtonPress?.(buttonId, 'joystick', { x, y, axis: button.axis });
    } else if (button?.isTouchpad) {
      onButtonPress?.(buttonId, 'touchpad', { x, y });
    } else {
      onButtonPress?.(buttonId, 'button');
    }
  };

  const handleButtonRelease = (buttonId, x, y) => {
    const button = config.buttons.find(b => b.id === buttonId);
    if (button?.isJoystick) {
      onButtonRelease?.(buttonId, 'joystick', { x, y, axis: button.axis });
    } else if (button?.isTouchpad) {
      onButtonRelease?.(buttonId, 'touchpad', { x, y });
    } else {
      onButtonRelease?.(buttonId, 'button');
    }
  };

  const handleContainerClick = (e) => {
    if (isEditMode && e.target === containerRef.current) {
      setSelectedButtonId(null);
    }
  };

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-full bg-gradient-to-br from-gray-900/50 to-slate-900/50 rounded-xl overflow-hidden border border-cyan-500/20 shadow-lg"
      onClick={handleContainerClick}
      style={{ touchAction: 'none' }}
    >
      {config.buttons.map((button) => (
        button.isTouchpad ? (
          <Touchpad
            key={button.id}
            touchpad={button}
            isEditMode={isEditMode}
            isSelected={selectedButtonId === button.id}
            onPress={handleButtonPress}
            onRelease={handleButtonRelease}
            onTap={onTouchpadTap}
            onSelect={setSelectedButtonId}
            onUpdate={onUpdateButton}
            onDelete={onDeleteButton}
            scale={scale}
            buttonScale={buttonScale}
          />
        ) : (
          <Button
            key={button.id}
            button={button}
            isEditMode={isEditMode}
            isSelected={selectedButtonId === button.id}
            onPress={handleButtonPress}
            onRelease={handleButtonRelease}
            onSelect={setSelectedButtonId}
            onUpdate={onUpdateButton}
            onDelete={onDeleteButton}
            scale={scale}
            buttonScale={buttonScale}
          />
        )
      ))}
      
      {config.buttons.length === 0 && isEditMode && (
        <div className="absolute inset-0 flex items-center justify-center text-white/50 text-lg">
          Click "Add Button" to start
        </div>
      )}
    </div>
  );
};

export default Controller;
