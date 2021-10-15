/*
  Serial Server
     - Respond to single character commands received via serial
*/
int rightWheelPin = 9;    // LED connected to digital pin 9
int leftWheelPin = 5;    // LED connected to digital pin 9

//float soundThreshold = 480;
int downTime = 350;

void setup() {
  // initialize serial port
  Serial.begin(19200);

  // Initialize output pins
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(rightWheelPin, OUTPUT);
  pinMode(leftWheelPin, OUTPUT);
}

void loop() {
  
  analogWrite(leftWheelPin, 255);
  analogWrite(rightWheelPin, 255);
 
  // Check for any incoming bytes
  if (Serial.available() > 0) {
    char newChar = Serial.read();

    // Respond to command "o"
    if(newChar == 'x') {
      // Turn off LED pin 13
      digitalWrite(LED_BUILTIN, LOW);
    }

    // Respond to command "x"
    if(newChar == 'o') {
      // Turn on LED pin 13
      digitalWrite(LED_BUILTIN, HIGH);
          
      analogWrite(rightWheelPin, 0);
      delay(downTime);        
    }
  }

  // Wait a bit
  delay(1);
}
