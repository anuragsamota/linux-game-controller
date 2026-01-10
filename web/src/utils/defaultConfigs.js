export const BUTTON_TYPES = {
  ACTION: 'action',
  DPAD: 'dpad',
  SHOULDER: 'shoulder',
  TRIGGER: 'trigger',
  SPECIAL: 'special',
  JOYSTICK: 'joystick',
  TOUCHPAD: 'touchpad',
};

export const DEFAULT_CONFIGS = [
  {
    id: 'standard-gamepad',
    name: 'Standard Gamepad',
    buttons: [
      { id: 'a', label: 'A', type: BUTTON_TYPES.ACTION, x: 75, y: 60, width: 8, height: 8, color: '#22c55e', scale: 1 },
      { id: 'b', label: 'B', type: BUTTON_TYPES.ACTION, x: 83, y: 52, width: 8, height: 8, color: '#ef4444', scale: 1 },
      { id: 'x', label: 'X', type: BUTTON_TYPES.ACTION, x: 67, y: 52, width: 8, height: 8, color: '#3b82f6', scale: 1 },
      { id: 'y', label: 'Y', type: BUTTON_TYPES.ACTION, x: 75, y: 44, width: 8, height: 8, color: '#eab308', scale: 1 },
      { id: 'dpad_up', label: '▲', type: BUTTON_TYPES.DPAD, x: 17, y: 44, width: 8, height: 8, color: '#94a3b8', scale: 1 },
      { id: 'dpad_down', label: '▼', type: BUTTON_TYPES.DPAD, x: 17, y: 60, width: 8, height: 8, color: '#94a3b8', scale: 1 },
      { id: 'dpad_left', label: '◄', type: BUTTON_TYPES.DPAD, x: 9, y: 52, width: 8, height: 8, color: '#94a3b8', scale: 1 },
      { id: 'dpad_right', label: '►', type: BUTTON_TYPES.DPAD, x: 25, y: 52, width: 8, height: 8, color: '#94a3b8', scale: 1 },
      { id: 'l1', label: 'L1', type: BUTTON_TYPES.SHOULDER, x: 10, y: 10, width: 12, height: 6, color: '#64748b', scale: 1 },
      { id: 'r1', label: 'R1', type: BUTTON_TYPES.SHOULDER, x: 78, y: 10, width: 12, height: 6, color: '#64748b', scale: 1 },
      { id: 'l2', label: 'L2', type: BUTTON_TYPES.TRIGGER, x: 10, y: 3, width: 12, height: 5, color: '#475569', scale: 1 },
      { id: 'r2', label: 'R2', type: BUTTON_TYPES.TRIGGER, x: 78, y: 3, width: 12, height: 5, color: '#475569', scale: 1 },
      { id: 'back', label: 'BACK', type: BUTTON_TYPES.SPECIAL, x: 35, y: 35, width: 10, height: 5, color: '#6366f1', scale: 1 },
      { id: 'start', label: 'START', type: BUTTON_TYPES.SPECIAL, x: 55, y: 35, width: 10, height: 5, color: '#6366f1', scale: 1 },
      { id: 'l3', label: 'L3', type: BUTTON_TYPES.JOYSTICK, x: 25, y: 70, width: 15, height: 15, color: '#8b5cf6', isJoystick: true, axis: 'left', scale: 1 },
      { id: 'r3', label: 'R3', type: BUTTON_TYPES.JOYSTICK, x: 60, y: 70, width: 15, height: 15, color: '#8b5cf6', isJoystick: true, axis: 'right', scale: 1 },
      { id: 'touchpad', label: 'TOUCH', type: BUTTON_TYPES.TOUCHPAD, x: 40, y: 20, width: 20, height: 15, color: '#9333ea', isTouchpad: true, scale: 1, sensitivity: 2.0, tapToClick: true },
    ],
  },
  {
    id: 'minimal',
    name: 'Minimal Controller',
    buttons: [
      { id: 'a', label: 'A', type: BUTTON_TYPES.ACTION, x: 70, y: 50, width: 12, height: 12, color: '#22c55e', scale: 1 },
      { id: 'b', label: 'B', type: BUTTON_TYPES.ACTION, x: 85, y: 50, width: 12, height: 12, color: '#ef4444', scale: 1 },
      { id: 'dpad_up', label: '▲', type: BUTTON_TYPES.DPAD, x: 15, y: 35, width: 10, height: 10, color: '#94a3b8', scale: 1 },
      { id: 'dpad_down', label: '▼', type: BUTTON_TYPES.DPAD, x: 15, y: 55, width: 10, height: 10, color: '#94a3b8', scale: 1 },
      { id: 'dpad_left', label: '◄', type: BUTTON_TYPES.DPAD, x: 5, y: 45, width: 10, height: 10, color: '#94a3b8', scale: 1 },
      { id: 'dpad_right', label: '►', type: BUTTON_TYPES.DPAD, x: 25, y: 45, width: 10, height: 10, color: '#94a3b8', scale: 1 },
    ],
  },
];

export const createNewConfig = (name = 'New Controller') => ({
  id: `config-${Date.now()}`,
  name,
  buttons: [],
});

export const createNewButton = (type = BUTTON_TYPES.ACTION) => {
  const defaults = {
    id: `btn-${Date.now()}`,
    label: 'BTN',
    type,
    x: 50,
    y: 50,
    width: 10,
    height: 10,
    color: '#3b82f6',
    scale: 1,
    isJoystick: type === BUTTON_TYPES.JOYSTICK,
    isTouchpad: type === BUTTON_TYPES.TOUCHPAD,
  };

  if (type === BUTTON_TYPES.JOYSTICK) {
    defaults.axis = 'left';
    defaults.width = 15;
    defaults.height = 15;
    defaults.label = 'L3';
  }

  if (type === BUTTON_TYPES.TOUCHPAD) {
    defaults.width = 20;
    defaults.height = 15;
    defaults.label = 'TOUCH';
    defaults.color = '#9333ea';
  }

  return defaults;
};
