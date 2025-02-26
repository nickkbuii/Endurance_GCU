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
    Weight(int DATA, int SCK, float CALIB_FACTOR) {
      scale.begin(DATA, SCK);
      scale.set_scale(CALIB_FACTOR);
      scale.tare();

      lastWeight = 0.0;
      lastTime = millis();
    }

    float getWeight(int sample_size) {
      if (scale.is_ready()) {
        return scale.get_units(sample_size);
      } else {
        Serial.println("WEIGHT NOT READY");
        return 0;
      }
    }

    float getMassFlowRate() {
      unsigned long currentTime = millis();
      float currentWeight = getWeight(5);
      float deltaWeight = currentWeight - lastWeight;
      float deltaTime = (currentTime - lastTime) / 1000.0;
      lastWeight = currentWeight;
      lastTime = currentTime;
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

#define SHUTDOWN_PIN 22
volatile bool shutDown;

void setup() {
  Serial.begin(57600);
  shutDown = false;

  pinMode(SHUTDOWN_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(SHUTDOWN_PIN), engineShutoffISR, FALLING);
  
  pump.start();
  engine.start();
  shutoff.start();
  propane.start();
  initializeActuators();
}

void loop() {  
  if (shutDown) {
    Serial.println("Shutting down...");
    engineShutoff();
  }

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
    } else if (command.startsWith("ENGINE_SHUTOFF:")) {
      Serial.println("SHUTOFF PRESET");
      engineShutoff();
    } else if (command.startsWith("ALL:")) {
      initializeActuators();
      delay(100);
      prestart(14, 17, 20, 17);
      delay(100);
      propanePhase(55, 45, 15, 25, 3000, 5000, 3000, 5000);
      delay(100);
      kerosenePhase(18, 18, 3000, 30000);
      delay(100);
      engineShutoff();
    }
  }

  // Send status of components to GUI
  Serial.println("TEMP:" + String(therm.getTemp()));
  Serial.println("PUMP:" + String(pump.getSpeed()));
  Serial.println("ENGINE:" + String(engine.getSpeed()));
  Serial.println("SHUTOFF:" + String(shutoff.getAngle()));
  Serial.println("PROPANE:" + String(propane.getAngle()));
  Serial.println("MASS:" + String(weight.getWeight(5)));
  delay(100);
}

void initializeActuators() {
  Serial.println("STATUS:INITIALIZING ACTUATORS");
  pump.run(0);
  engine.run(0);
  propane.rotate(75);
}

// PRESET: shutoff engine
void engineShutoff() {
  Serial.println("STATUS:SHUTTING OFF ENGINE");
  propane.rotate(75);
  pump.run(0);
  engine.run(0);
}

// PRESET: engine pre-start
void prestart(int engineIdle, int pumpIdle, int pumpPhase1, int pumpPhase2) {
  Serial.println("STATUS:PRE-START");
  if (shutDown) return;
  initializeActuators();
  if (shutDown) return;
  engine.run(engineIdle);
  if (shutDown) return;
  pump.run(pumpIdle);
  if (shutDown) return;
  pump.run(pumpPhase1);
  if (shutDown) return;
  delay(3000);
  if (shutDown) return;
  pump.run(pumpPhase2);
}

// PRESET: propane phase
void propanePhase(int propanePhase1, int propanePhase2, int enginePhase1, int enginePhase2, int delay1, int delay2, int delay3, int delay4) {
  Serial.println("STATUS:PROPANE-PHASE");
  if (shutDown) return;
  propane.rotate(propanePhase1);
  if (shutDown) return;
  delay(delay1);
  if (shutDown) return;
  engine.run(enginePhase1);
  if (shutDown) return;  
  delay(delay2);
  if (shutDown) return;
  propane.rotate(propanePhase2);
  if (shutDown) return;
  delay(delay3);
  if (shutDown) return;
  engine.run(enginePhase2);
  if (shutDown) return;
  delay(delay4);

  if (shutDown) return;
  int startSpeed = enginePhase2 / 10 * 10;
  float dt = 100/(90 - startSpeed) * 1000;
  for (int i = startSpeed; i <= 90; i += 10) {
    if (shutDown) return;
    engine.run(i);
    delay(dt);
  }
}

// PRESET: kerosene phase
void kerosenePhase(int pumpPhase1, int pumpPhase2, int delay1, int engineHoldTime) {
  Serial.println("STATUS:KEROSENE-PHASE");
  if (shutDown) return;
  pump.run(pumpPhase1);
  if (shutDown) return;
  delay(delay1);
  if (shutDown) return;
  propane.rotate(75);
  if (shutDown) return;
  pump.run(pumpPhase2);
  if (shutDown) return;
  delay(engineHoldTime);
}

// Interrupt Service Routine
void engineShutoffISR() {
    Serial.println("ISR");
    shutDown = true;
}