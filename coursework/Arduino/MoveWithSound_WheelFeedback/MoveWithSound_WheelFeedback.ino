#include <Metro.h>

int rightWheelPin = 9;    // LED connected to digital pin 9
int leftWheelPin = 5;    // LED connected to digital pin 9
float soundThreshold = 480;
int downTime = 150;
const byte ledPin = 13;
const byte interruptPin = 2;
volatile byte state = HIGH;
int ledOutputPin = 12;
int d = 0;
int speed; 


Metro met = Metro(50);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  //pinMode(leftPin1, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(interruptPin, INPUT_PULLUP);
  pinMode(ledOutputPin, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(interruptPin), blink, CHANGE);
}
void loop() {
   // put your main code here, to run repeatedly:
   analogWrite(leftWheelPin, 255);

   int sensorValue = analogRead(A0);

   if (sensorValue > soundThreshold){   
       analogWrite(rightWheelPin, 0);
       delay(downTime);        // delay in between reads for stability
   } else {
       analogWrite(rightWheelPin, 255);
   }

   //int encoder = digitalRead(interruptPin);

   //time = millis();
   if (met.check()){
       speed = d;
       d = 0; 
       Serial.println(speed);
    
   }
   //speed = d/time;

   if (speed == 0){
       digitalWrite(ledOutputPin, HIGH);
   }
   else{
       digitalWrite(ledOutputPin, LOW);
   }
   digitalWrite(ledPin, state);
   delay(1);        // delay in between reads for stability
  
}
void blink() {
  state = !state;
  d++;
  
}
