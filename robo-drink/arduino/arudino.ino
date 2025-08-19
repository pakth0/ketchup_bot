// Arduino sketch (save as arduino/solenoid_control.ino)
const int SOLENOID_PIN = 2;  // Pin 2 for power

void setup() {
  Serial.begin(9600);
  pinMode(SOLENOID_PIN, OUTPUT);
  digitalWrite(SOLENOID_PIN, LOW);  // Start with solenoid off
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '1') {
      digitalWrite(SOLENOID_PIN, HIGH);  // Turn on pin 2
      Serial.println("Solenoid ON");
    }
    else if (command == '0') {
      digitalWrite(SOLENOID_PIN, LOW);   // Turn off pin 2
      Serial.println("Solenoid OFF");
    }
  }
}