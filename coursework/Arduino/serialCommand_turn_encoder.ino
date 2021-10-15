/*
  Serial Server
     - Respond to single character commands received via serial
*/

#include <Metro.h>

int rightWheelPin = 9;  //wheels
int leftWheelPin = 5;    

int faceLed = 13;
const byte interruptPinLeft = 2; //encoder left
const byte interruptPinRight = 3; //encoder right

int turnLedLeft = 6;
int turnLedRight = 7;

volatile byte stateLeft = HIGH; 
volatile byte stateRight = HIGH; 

int distLeft = 0;
int distRight = 0;
int speedLeft;
int speedRight;

int downTime = 350;

Metro met = Metro(50);

void setup() {
  // initialize serial port
  Serial.begin(19200);

  // Initialize output pins
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(rightWheelPin, OUTPUT);
  pinMode(leftWheelPin, OUTPUT);
  pinMode(faceLed, OUTPUT);
  pinMode(interruptPinLeft, INPUT_PULLUP);
  pinMode(interruptPinRight, INPUT_PULLUP);
  pinMode(turnLedLeft, OUTPUT);
  pinMode(turnLedRight, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(interruptPinLeft), blinkLeft, CHANGE);
  attachInterrupt(digitalPinToInterrupt(interruptPinRight), blinkRight, CHANGE);


}

void loop() {

  //set wheels to go at the beginning
  digitalWrite(leftWheelPin, HIGH);
  digitalWrite(rightWheelPin, HIGH);

   
  // Check for signal that face detected
  if (Serial.available() > 0) {
    char newChar = Serial.read();

    if(newChar == 'x') {     
      digitalWrite(faceLed, LOW);      
    }
    if(newChar == 'o') {
      // Turn on LED pin 13
      digitalWrite(LED_BUILTIN, HIGH);          
      digitalWrite(rightWheelPin, 0);
      delay(downTime);        
    }
  }

  //check if wheel is moving, if not, turn on the turnLed
  if (met.check()){
       speedLeft = distLeft;
       speedRight = distRight;
       distLeft = 0; 
       distRight = 0; 
       Serial.println(speedRight);
    
   }
   //speed = d/time;

   if (speedLeft == 0){
       digitalWrite(turnLedLeft, HIGH);
   }
   else{
       digitalWrite(turnLedLeft, LOW);
   }

   if (speedRight == 0){
       digitalWrite(turnLedRight, HIGH);
   }
   else{
       digitalWrite(turnLedRight, LOW);
   }
  

  // Wait a bit
  delay(1);
}


void blinkLeft() {
  stateLeft = !stateLeft;
  distLeft++;  
}

void blinkRight() {
  stateRight = !stateRight;
  distRight++;  
}
