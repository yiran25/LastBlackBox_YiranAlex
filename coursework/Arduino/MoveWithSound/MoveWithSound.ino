
int rightWheelPin = 9;    // LED connected to digital pin 9

int leftWheelPin = 5;    // LED connected to digital pin 9

float soundThreshold = 480;
int downTime = 150;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  //pinMode(leftPin1, OUTPUT);


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
   
   Serial.println(sensorValue);
   delay(1);        // delay in between reads for stability
  
}
