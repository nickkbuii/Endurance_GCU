#include <Servo.h>
#include "max6675.h"

class Thermocouple {
  public:
    Thermocouple(int SO, int CS, int SCK):
      thermo(SCK, CS, SO) {}

    float getTemp() {
      float temp = thermo.readCelsius();
      return temp;
    }

    MAX6675 thermo;
};

class Pump {
  public:
    Pump(int enA, int in1, int in2):
      enA(enA),
      in1(in1),
      in2(in2) {}

    void start() {
      pinMode(enA, OUTPUT);
      pinMode(in1, OUTPUT);
	    pinMode(in2, OUTPUT);
    }

    void run(int speed) {
      // Ensure speed is between 0 and 100
      speed = constrain(speed, 0, 100);
      currentSpeed = speed;
      analogWrite(enA, map(speed, 0, 100, 0, 255)); // Map to PWM range
      digitalWrite(in1, HIGH);
      digitalWrite(in2, LOW);
    }
    

    void stop() {
      digitalWrite(in1, LOW);
      digitalWrite(in2, LOW);
    }

    int getSpeed() {
      return currentSpeed;
    }

  private:
    int enA;
    int in1;
    int in2;
    int currentSpeed;
};

class ServoMotor {
  public:
    ServoMotor(int servoPin):
      servoPin(servoPin) {}
    
    void start() {
      servo.attach(servoPin);
    }

    void rotate(int degrees) {
      degrees = constrain(degrees, 0, 180);
      currentAngle = degrees;
      servo.write(degrees);
    }

    int getAngle() {
      return currentAngle;
    }

  private:
    int servoPin;  
    Servo servo;
    int currentAngle;
};

class Engine {
  public: 
    Engine(int escPin):
      escPin(escPin){}
    
    void start() {
      esc.attach(escPin);
      esc.writeMicroseconds(1000);
    }

    void run(int speed) {
      speed = constrain(speed, 1000, 2000);
      currentSpeed = speed;
      esc.writeMicroseconds(speed);
    }

    int getSpeed() {
      return currentSpeed;
    }


  private:
    Servo esc;
    int escPin;
    int currentSpeed;
};

Thermocouple therm(3, 10, 13);
Pump pump(4, 5, 6);
Engine engine(7);
ServoMotor shutoff(8);
ServoMotor propane(9);

void setup() {
  Serial.begin(9600);
  pump.start();
  engine.start();
  shutoff.start();
  propane.start();
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');  // Read command from GUI
    if (command.startsWith("PUMP:")) {
      int speed = command.substring(5).toInt();    // Extract pump speed
      pump.run(speed);
    } else if (command.startsWith("ENGINE:")) {
      int speed = command.substring(7).toInt();    // Extract engine speed
      engine.run(speed);
    } else if (command.startsWith("SHUTOFF:")) {
      int angle = command.substring(8).toInt();    // Extract shutoff angle
      shutoff.rotate(angle);
    } else if (command.startsWith("PROPANE:")) {
      int angle = command.substring(8).toInt();    // Extract propane angle
      propane.rotate(angle);
    }
  }

  // Send the thermocouple temperature to GUI
  Serial.println("TEMP:" + String(therm.getTemp(), 2)); // Send temperature with 2 decimal places

  // Send the current pump speed to GUI
  Serial.println("PUMP:" + String(pump.getSpeed())); // Assuming you have a getSpeed() method for the pump
  
  // Send the current engine speed to GUI
  Serial.println("ENGINE:" + String(engine.getSpeed())); // Assuming you have a getSpeed() method for the engine
  
  // Send the current shutoff angle to GUI
  Serial.println("SHUTOFF:" + String(shutoff.getAngle())); // Assuming you have a getAngle() method for shutoff
  
  // Send the current propane angle to GUI
  Serial.println("PROPANE:" + String(propane.getAngle())); // Assuming you have a getAngle() method for propane

  delay(100); // Delay to avoid flooding the serial port
}