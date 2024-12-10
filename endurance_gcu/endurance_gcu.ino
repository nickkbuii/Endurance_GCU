#include <Servo.h>
#include "max6675.h"

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
      analogWrite(enA, speed);
      digitalWrite(in1, HIGH);
      digitalWrite(in2, LOW);
    }

    void stop() {
      digitalWrite(in1, LOW);
      digitalWrite(in2, LOW);
    }

  private:
    int enA;
    int in1;
    int in2;
};

class Flow {
  public:

    Flow(int flowPin, unsigned long samplingInterval, float calibrationFactor, float density):
      flowPin(flowPin),
      samplingInterval(samplingInterval),
      calibrationFactor(calibrationFactor),
      density(density),
      lastTime(0),
      flowRate(0.0) {}

    static void pulse() {
      pulseCount++;
    }

    void start() {
      pinMode(flowPin, INPUT);
      attachInterrupt(digitalPinToInterrupt(flowPin), pulse, FALLING);
    }

    float getFlow() {
      if (millis() - lastTime >= samplingInterval) {
        detachInterrupt(digitalPinToInterrupt(flowPin));

        flowRate = (float)pulseCount / (samplingInterval / 1000.0); // mL per sec

        // reset pulse count and timer
        pulseCount = 0;
        lastTime = millis();

        attachInterrupt(digitalPinToInterrupt(flowPin), pulse, FALLING);

        return flowRate;
      }
      return flowRate;
    }

    float getMassFlow() {
        return getFlow() * density;
    }

  private:
    int flowPin;
    volatile static int pulseCount;
    unsigned long lastTime;
    unsigned long samplingInterval;
    float flowRate;
    float calibrationFactor;
    float density;
};

class Shutoff {
  public:
    Shutoff(int shutoffPin):
      shutoffPin(shutoffPin) {}
    
    void start() {
      shutoff.attach(shutoffPin);
    }

    void rotate(int degrees) {
      shutoff.write(degrees);
      delay(1000);
    }

  private:
    int shutoffPin;  
    Servo shutoff;
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
      esc.writeMicroseconds(speed);
      delay(50);
    }

  private:
    Servo esc;
    int escPin;
};

Thermocouple therm(3, 10, 13);
Pump pump(4, 5, 6);
Flow flow(2, 1000, 1.0, 0.82);
Shutoff shutoff(8);
Engine engine(7);

volatile int Flow::pulseCount = 0;

void setup() {
  Serial.begin(9600);
  pump.start();
  flow.start();
  shutoff.start();
  engine.start();
}

void loop() {
  // Integration Tests
  Serial.println("Celsius: " + String(therm.getTemp()));

  pump.run(255);
  pump.stop();

  Serial.println("FLow Rate " + String(flow.getFlow()));
  Serial.println("Mass Flow Rate: " + String(flow.getMassFlow()));

  shutoff.rotate(90);
  shutoff.rotate(0);

  for (int i = 1000; i <= 2000; i+=10) {
    engine.run(i);
  }
}