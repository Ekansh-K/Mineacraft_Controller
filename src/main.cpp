// ESP32 Dual Joystick BLE Controller using BLE CompositeHID with NimBLE 
// Separate keyboard and mouse devices in one composite HID for maximum compatibility

#include <Arduino.h>
#include <BleCompositeHID.h>
#include <KeyboardDevice.h>
#include <MouseDevice.h>

// Hardware pin definitions
#define LEFT_X_PIN    27    // Movement joystick X-axis (WASD)
#define LEFT_Y_PIN    25    // Movement joystick Y-axis (WASD)
#define RIGHT_X_PIN   34    // Camera joystick X-axis (Mouse) - ADC1_CH6
#define RIGHT_Y_PIN   32    // Camera joystick Y-axis (Mouse) - ADC1_CH4
#define RIGHT_BTN     13    // Right joystick button -> Space
#define RECAL_BTN     12     // Recalibration button (hold >1.5s)

// Configuration constants
#define DEFAULT_CENTER      1900    // Default center based on previous observations
#define DEADZONE           300     // Deadzone around center for noise
#define WASD_THRESHOLD     500     // Threshold for WASD activation
#define HYSTERESIS         80      // Hysteresis to prevent key chatter
#define MOUSE_SENSITIVITY  12      // Mouse movement sensitivity multiplier (increased for higher sensitivity)
#define MOUSE_MAX_STEP     8       // Maximum mouse step per loop
#define DEBOUNCE_TIME      50      // Button debounce time in ms
// #define CALIBRATION_SAMPLES 150    // Samples for calibration averaging - not used (manual recal disabled)
// #define RECAL_HOLD_TIME    1500    // Hold time for recalibration (ms) - not used (manual recal disabled)

// Axis calibration structure
struct AxisCalibration {
  int center = DEFAULT_CENTER;
  int pressThresholdHigh;    // center + threshold + hysteresis
  int releaseThresholdHigh;  // center + threshold - hysteresis
  int pressThresholdLow;     // center - threshold - hysteresis
  int releaseThresholdLow;   // center - threshold + hysteresis
};

// Global variables
// unsigned long recalStartTime = 0;  // Not needed - manual recalibration disabled

// Axis calibration data
AxisCalibration leftX, leftY, rightX, rightY;

// WASD key states for proper press/release
bool wPressed = false, aPressed = false, sPressed = false, dPressed = false;
bool spacePressed = false;

// Mouse smoothing
float mouseXFilter = 0.0f, mouseYFilter = 0.0f;
const float MOUSE_EMA_ALPHA = 0.25f;

// BLE CompositeHID setup
KeyboardDevice keyboard;
MouseDevice mouse;
BleCompositeHID compositeHID("ESP32 Game Controller", "ESP32", 100);

// Utility functions
int clampValue(int value, int minVal, int maxVal) {
  return value < minVal ? minVal : (value > maxVal ? maxVal : value);
}

// Calibration functions
int readSimpleAverage(int pin, int samples) {
  int sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return clampValue(sum / samples, 0, 4095);
}

/*
// Trimmed average function - disabled, using only simple average for initial calibration
int readTrimmedAverage(int pin, int samples) {
  int minVal = 4095, maxVal = 0, sum = 0;
  for (int i = 0; i < samples; i++) {
    int value = analogRead(pin);
    if (value < minVal) minVal = value;
    if (value > maxVal) maxVal = value;
    sum += value;
    delay(2);
  }
  // Remove min and max, average the rest
  sum -= (minVal + maxVal);
  return clampValue(sum / (samples - 2), 0, 4095);
}
*/

void computeThresholds(AxisCalibration &axis) {
  axis.pressThresholdHigh = axis.center + WASD_THRESHOLD + HYSTERESIS;
  axis.releaseThresholdHigh = axis.center + WASD_THRESHOLD - HYSTERESIS;
  axis.pressThresholdLow = axis.center - WASD_THRESHOLD - HYSTERESIS;
  axis.releaseThresholdLow = axis.center - WASD_THRESHOLD + HYSTERESIS;
}

void calibrateAxisInitial(int pin, AxisCalibration &axis) {
  axis.center = readSimpleAverage(pin, 10);  // Quick 10-sample average for startup
  computeThresholds(axis);
}

/*
// Full calibration function - disabled, using only initial calibration  
void calibrateAxis(int pin, AxisCalibration &axis) {
  axis.center = readTrimmedAverage(pin, CALIBRATION_SAMPLES);  // Full calibration for recal button
  computeThresholds(axis);
}
*/

void initialCalibration() {
  Serial.println("Quick initial calibration... Keep joysticks centered!");
  
  calibrateAxisInitial(LEFT_X_PIN, leftX);
  calibrateAxisInitial(LEFT_Y_PIN, leftY);
  calibrateAxisInitial(RIGHT_X_PIN, rightX);
  calibrateAxisInitial(RIGHT_Y_PIN, rightY);
  
  Serial.printf("Initial calibration complete:\n");
  Serial.printf("Left stick center: X=%d, Y=%d\n", leftX.center, leftY.center);
  Serial.printf("Right stick center: X=%d, Y=%d\n", rightX.center, rightY.center);
}

/*
// Full recalibration function - disabled, using only initial calibration
void calibrateAllAxes() {
  Serial.println("Full recalibration... Keep joysticks centered!");
  
  calibrateAxis(LEFT_X_PIN, leftX);
  calibrateAxis(LEFT_Y_PIN, leftY);
  calibrateAxis(RIGHT_X_PIN, rightX);
  calibrateAxis(RIGHT_Y_PIN, rightY);
  
  Serial.printf("Full recalibration complete:\n");
  Serial.printf("Left stick center: X=%d, Y=%d\n", leftX.center, leftY.center);
  Serial.printf("Right stick center: X=%d, Y=%d\n", rightX.center, rightY.center);
}
*/

// Input handling functions
/*
// Manual recalibration disabled - using only initial 10-reading calibration
void handleRecalibrationButton() {
  bool buttonState = digitalRead(RECAL_BTN) == LOW;
  unsigned long currentTime = millis();
  
  if (buttonState) {
    if (recalStartTime == 0) {
      recalStartTime = currentTime;
    } else if (currentTime - recalStartTime > RECAL_HOLD_TIME) {
      calibrateAllAxes();
      recalStartTime = currentTime + 60000; // Prevent retrigger for 1 minute
    }
  } else {
    recalStartTime = 0;
  }
}
*/

void handleWASDMovement(int xValue, int yValue) {
  // Handle W key (Forward) - Y axis positive
  if (yValue > leftY.pressThresholdHigh && !wPressed) {
    keyboard.keyPress(KEY_W);
    wPressed = true;
    Serial.println("W pressed");
  } else if (yValue < leftY.releaseThresholdHigh && wPressed) {
    keyboard.keyRelease(KEY_W);
    wPressed = false;
    Serial.println("W released");
  }
  
  // Handle S key (Backward) - Y axis negative
  if (yValue < leftY.pressThresholdLow && !sPressed) {
    keyboard.keyPress(KEY_S);
    sPressed = true;
    Serial.println("S pressed");
  } else if (yValue > leftY.releaseThresholdLow && sPressed) {
    keyboard.keyRelease(KEY_S);
    sPressed = false;
    Serial.println("S released");
  }
  
  // Handle A key (Left) - X axis negative
  if (xValue < leftX.pressThresholdLow && !aPressed) {
    keyboard.keyPress(KEY_A);
    aPressed = true;
    Serial.println("A pressed");
  } else if (xValue > leftX.releaseThresholdLow && aPressed) {
    keyboard.keyRelease(KEY_A);
    aPressed = false;
    Serial.println("A released");
  }
  
  // Handle D key (Right) - X axis positive
  if (xValue > leftX.pressThresholdHigh && !dPressed) {
    keyboard.keyPress(KEY_D);
    dPressed = true;
    Serial.println("D pressed");
  } else if (xValue < leftX.releaseThresholdHigh && dPressed) {
    keyboard.keyRelease(KEY_D);
    dPressed = false;
    Serial.println("D released");
  }
}

void handleMouseMovement(int xValue, int yValue) {
  // Convert to movement relative to center
  int deltaX = xValue - rightX.center;
  int deltaY = yValue - rightY.center;
  
  // Apply deadzone to prevent jitter
  if (abs(deltaX) < DEADZONE) deltaX = 0;
  if (abs(deltaY) < DEADZONE) deltaY = 0;
  
  // Scale movement for mouse sensitivity
  float rawMouseX = (float)(deltaX * MOUSE_SENSITIVITY) / 200.0f;
  float rawMouseY = (float)(deltaY * MOUSE_SENSITIVITY) / 200.0f;
  
  // Apply exponential moving average for smoothing
  mouseXFilter = mouseXFilter * (1.0f - MOUSE_EMA_ALPHA) + rawMouseX * MOUSE_EMA_ALPHA;
  mouseYFilter = mouseYFilter * (1.0f - MOUSE_EMA_ALPHA) + rawMouseY * MOUSE_EMA_ALPHA;
  
  // Convert to integer steps and clamp
  int mouseStepX = clampValue((int)round(mouseXFilter), -MOUSE_MAX_STEP, MOUSE_MAX_STEP);
  int mouseStepY = clampValue((int)round(mouseYFilter), -MOUSE_MAX_STEP, MOUSE_MAX_STEP);
  
  // Send mouse movement if there's any
  if (mouseStepX != 0 || mouseStepY != 0) {
    mouse.mouseMove(mouseStepX, mouseStepY);
  }
}

void handleSpaceButton() {
  bool buttonState = digitalRead(RIGHT_BTN) == LOW;
  
  if (buttonState && !spacePressed) {
    keyboard.keyPress(KEY_SPACE);
    spacePressed = true;
    Serial.println("Space pressed");
  } else if (!buttonState && spacePressed) {
    keyboard.keyRelease(KEY_SPACE);
    spacePressed = false;
    Serial.println("Space released");
  }
}

void handleKeyboardMouseMode() {
  // Read analog values from joysticks
  int leftXValue = analogRead(LEFT_X_PIN);
  int leftYValue = analogRead(LEFT_Y_PIN);
  int rightXValue = analogRead(RIGHT_X_PIN);
  int rightYValue = analogRead(RIGHT_Y_PIN);
  
  // Handle WASD movement (left joystick)
  handleWASDMovement(leftXValue, leftYValue);
  
  // Handle mouse movement (right joystick)
  handleMouseMovement(rightXValue, rightYValue);
  
  // Handle space button (right joystick button)
  handleSpaceButton();
}

void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 Dual Joystick BLE CompositeHID Controller Starting...");
  
  // Initialize pins
  // pinMode(RECAL_BTN, INPUT_PULLUP);  // Manual recalibration disabled
  pinMode(RIGHT_BTN, INPUT_PULLUP);
  
  // Add devices to composite HID
  compositeHID.addDevice(&keyboard);
  compositeHID.addDevice(&mouse);
  
  // Start the composite HID device
  compositeHID.begin();
  
  // Quick initial calibration on boot (just 10 readings)
  initialCalibration();
  
  Serial.println("BLE CompositeHID Controller ready! Pairing mode active.");
}

void loop() {
  // Manual recalibration disabled - using only initial calibration
  // handleRecalibrationButton();
  
  // Only process joysticks when connected
  if (compositeHID.isConnected()) {
    handleKeyboardMouseMode();
  }
  
  delay(10); // Small delay for stability
}
