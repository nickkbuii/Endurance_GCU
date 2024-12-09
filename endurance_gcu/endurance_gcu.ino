// #include <Servo.h>
// #include "max6675.h"

// // vars for fill pump (12V DC motor)
// const int enA = 4; // speed
// const int in1 = 5; // direction 1
// const int in2 = 6; // direction 2

// // vars for flow sensor
// const int sensorPin = 2; // flow sensor signal pin
// volatile int pulseCount = 0; // pulse count
// unsigned long lastTime = 0; // time of last sample
// const unsigned long samplingInterval = 1000; // sampling interval: 1 sec
// float flowRate = 0.0; // flow rate in mL/s
// const float calibrationFactor = 1.0; // pulse per mL
// const float keroseneDensity = 0.82; // kerosene density for mass flow rate calc

// // vars for engine
// Servo esc;
// const int escPin = 7;

// vars for thermocouple
// int thermoDO = 3;
// int thermoCS = 10;
// int thermoCLK = 13;

// MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

// void setup() {
//   Serial.begin(9600);
//   delay(500);
// }

// void loop() {
//   Serial.print("C = ");
//   Serial.println(thermocouple.readCelsius());
//   delay(250);
// }


// // vars for shutoff/propane
// Servo shutoff;
// void setup() {
//   shutoff.attach(8);
// }

// void loop() {
//   shutoff.write(90);
//   delay(1000);
//   shutoff.write(180);
//   delay(1000);
//   shutoff.write(0);
//   delay(1000);
// }

// void setup() {
//   esc.attach(escPin);
//   Serial.begin(9600);

//   esc.writeMicroseconds(1000);
//   delay(2000);
// }

// void loop() {
//   // Increase throttle
//   for (int speed = 1000; speed <= 2000; speed += 10) {
//     esc.writeMicroseconds(speed);
//     Serial.println(speed);
//     delay(50);
//   }

//   // Decrease throttle
//   for (int speed = 2000; speed >= 1000; speed -= 10) {
//     esc.writeMicroseconds(speed);
//     Serial.println(speed);
//     delay(50);
//   }
// }

// void setup() {
//   pinMode(enA, OUTPUT);
//   pinMode(in1, OUTPUT);
// 	 pinMode(in2, OUTPUT);
// }

// void loop() {
//   direction();
//   delay(1000);
// }

// void direction(){
//   analogWrite(enA, 255);
//   digitalWrite(in1, HIGH);
//   digitalWrite(in2, LOW);
//   delay(2000);

//   digitalWrite(in1, LOW);
// 	digitalWrite(in2, LOW);
// }

// void pulseCounter() {
//   pulseCount++;
// }

// void setup() {
//   pinMode(sensorPin, INPUT);
//   attachInterrupt(digitalPinToInterrupt(sensorPin), pulseCounter, FALLING);
//   Serial.begin(9600);
// }

// void loop() {
//   if (millis() - lastTime >= samplingInterval) {
//     detachInterrupt(digitalPinToInterrupt(sensorPin));

//     // Calculate flow rate in mL/s
//     flowRate = (float)pulseCount / (samplingInterval / 1000.0); // mL per second

//     // Print the flow rate
//     Serial.print("Flow rate: ");
//     Serial.print(flowRate * 60, 2); // Display with two decimal places
//     Serial.println(" mL/min");

//     Serial.print("Mass Flow Rate: ");
//     Serial.print(flowRate * 60 * keroseneDensity, 3);
//     Serial.println(" g/min");

//     // Reset pulse count and timer
//     pulseCount = 0;
//     lastTime = millis();

//     attachInterrupt(digitalPinToInterrupt(sensorPin), pulseCounter, FALLING);
//   }
// }
