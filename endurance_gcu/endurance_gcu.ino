#include <Servo.h>
#include <Arduino.h>
#include "max6675.h"
#include "HX711.h"

class Thermocouple {
  public:
    Thermocouple(int SO, int CS, int SCK):
      thermo(SCK, CS, SO) {}

    float getTemp() {
      float temp = thermo.readCelsius();
      delay(250);
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
      currentSpeed = speed;
      speed = map(speed, 0, 100, 0, 255);
      analogWrite(enA, speed);
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
      currentSpeed = speed;
      speed = map(speed, 0, 100, 1000, 2000);
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

class Weight {
  public:
    Weight() {
      lastTime = millis();
      lastWeight = 0.0;
    }

    float getWeight() {
      Serial2.print("W\r");
      if (Serial2.available() > 0) {
        String weightData = "";
        while (Serial2.available()) {
          char received = Serial2.read();
          weightData += received;
        }
        return extractWeight(weightData);
      }
      return -1;
    }

    float getMassFlowRate() {
        unsigned long currTime = millis();
        float currWeight = getWeight();
        float dW = currWeight - lastWeight;
        float dT = (currTime - lastTime) / 1000.0;
        lastTime = currTime;
        lastWeight = currWeight;
        float flowRate = (dT > 0) ? (dW / dT) : 0;
        if (abs(flowRate) < 0.1) flowRate = 0;
        
        return flowRate;
    }

  private:
    unsigned long lastTime;
    float lastWeight;

    float extractWeight(String data) {
      data.trim();
      int spaceIndex = data.indexOf(' ');
      if (spaceIndex != -1) {
        String weightString = data.substring(spaceIndex);
        weightString.trim();
        return weightString.toFloat();
      }
      return 0.0;
    }
};

Weight weight;
Thermocouple therm(3, 10, 13);
Pump pump(4, 5, 6);
Engine engine(7);
ServoMotor shutoff(8);
ServoMotor propane(9);

void setup() {
  Serial.begin(57600);
  Serial2.begin(9600);
  pump.start();
  engine.start();
  shutoff.start();
  propane.start();
  initializeActuators();
}

void loop() {  
  // Read command from GUI and execute cooresponding action
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("PUMP:")) {
      int speed = command.substring(5).toInt();
      pump.run(speed);
    } else if (command.startsWith("ENGINE:")) {
      int speed = command.substring(7).toInt();
      engine.run(speed);
    } else if (command.startsWith("SHUTOFF:")) {
      int angle = command.substring(8).toInt();
      shutoff.rotate(angle);
    } else if (command.startsWith("PROPANE:")) {
      int angle = command.substring(8).toInt();
      propane.rotate(angle);
    } 
  }

  // Send status of components to GUI
  Serial.println("TEMP:" + String(therm.getTemp()));
  Serial.println("PUMP:" + String(pump.getSpeed()));
  Serial.println("ENGINE:" + String(engine.getSpeed()));
  Serial.println("SHUTOFF:" + String(shutoff.getAngle()));
  Serial.println("PROPANE:" + String(propane.getAngle()));
  Serial.println("MASS:" + String(weight.getWeight()));
  Serial.println("MASS FLOW:" + String(weight.getMassFlowRate()));
  delay(100);
}

void initializeActuators() {
  Serial.println("STATUS:INITIALIZING ACTUATORS");
  pump.run(0);
  engine.run(0);
  propane.rotate(75);
}