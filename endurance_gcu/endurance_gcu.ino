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
      speed = (1.0 * speed / 100) * 255;
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
      speed = (1 + (1.0*speed/100)) * 1000;
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
    Weight(int DATA, int SCK, float CALIB_FACTOR) {
      scale.begin(DATA, SCK);
      scale.set_scale(CALIB_FACTOR);
      scale.tare();

      lastWeight = 0.0;
      lastTime = millis();
    }

    float getWeight() {
      if (scale.is_ready()) {
        return scale.get_units();
      } else {
        Serial.println("WEIGHT NOT READY");
        return 0;
      }
    }

    float getMassFlowRate(int sampling_interval) {
      unsigned long currentTime = millis();
      float currentWeight = getWeight();
      float deltaWeight = currentWeight - lastWeight;
      float deltaTime = abs(currentTime - lastTime) / 1000.0;
      lastWeight = currentWeight;
      lastTime = currentTime;
      delay(10);
      return (deltaTime > 0) ? (deltaWeight / deltaTime) : 0;
    }

  private:
    HX711 scale;
    float lastWeight;
    unsigned long lastTime;
};

Weight weight(2, 45, 741.2608696);
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
  // Read command from GUI and extract control inputs
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
  Serial.println("WEIGHT:" + String(weight.getMassFlowRate(5)));
  delay(100);
}