/*
 
  https://www.arduino.cc/en/Tutorial/BuiltInExamples/Blink
*/

//array thresholds = [350,400,450,500,550,600,650,700,750,800];
int thresholds[] = {
  100,150,200,250,300,350,400,500,550,600,650,700,750,800,850,900,950,1000
};
int delays[] = {
  1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18

};
int size1 = sizeof(delays)/sizeof(int);
// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(12, OUTPUT);
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
}

// the loop function runs over and over again forever
void loop() {
  
  int sensorValue = analogRead(A0);

  if (sensorValue < thresholds[0]){
      digitalWrite(12, HIGH); 
      delay(delays[0]);
      digitalWrite(12, LOW);    // turn the LED off by making the voltage LOW
      delay(delays[0]);      
  } 
  for (int i = 1; i < size1-2; i++){
      if (sensorValue > thresholds[i] && sensorValue > thresholds[i+1]){
        digitalWrite(12, HIGH); 
        delay(delays[i]);
        digitalWrite(12, LOW);    // turn the LED off by making the voltage LOW
        delay(delays[i]);    
      // wait for a second
  
      }
   }
   if (sensorValue > thresholds[size1-1]){
      digitalWrite(12, HIGH); 
      delay(delays[size1-1]);
      digitalWrite(12, LOW);    // turn the LED off by making the voltage LOW
      delay(delays[size1-1]);      
  } 
  delay(3);        // delay in between reads for stability
  Serial.println(sensorValue);
}
//else if (sensorValue > thresholds[0] && sensorValue > thresholds[1] ){                  // wait for a second
      //digitalWrite(12, HIGH); 
      //delay(2);
      //digitalWrite(12, LOW);    // turn the LED off by making the voltage LOW
      //delay(2);
//  }                
