#include <DHT.h>

#include <VirtualWire.h>

#define DHT22_PIN 6

const int led_pin = 13;
const int transmit_pin = 12;
const int receive_pin = 11;
const int transmit_en_pin = 3;
const int photo_pin = A0;

DHT dht(DHT22_PIN, DHT22);

void setup()
{
    delay(1000);
    Serial.begin(9600);  // Debugging only
    Serial.println("setup");

    pinMode(photo_pin, INPUT);
    dht.begin();

    // Initialise the IO and ISR
    vw_set_tx_pin(transmit_pin);
    vw_set_rx_pin(receive_pin);
    vw_set_ptt_pin(transmit_en_pin);
    vw_set_ptt_inverted(true); // Required for DR3100
    vw_setup(2000);  // Bits per sec

    vw_rx_start();       // Start the receiver PLL running
}

/// DATA PACKET
/// bytes: [protocol version][board id][seq id][app id][recipient board id][value byte 0][value byte 1] ...

void serial_send(uint8_t* buf, uint8_t buflen)
{
  for (int i = 0; i < buflen; i++)
  {
      Serial.print(buf[i]);
      Serial.print(' ');
  }
  
  Serial.println();
}

unsigned long photores_time = 0;
int photores_v = 0;
unsigned long photolastsendtime = 0;


unsigned long dht_time = 0;
int dht_t = 0;
int dht_h = 0;
unsigned long dht_lastsendtime = 0;

uint8_t seq = 0;


void loop()
{
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    if (vw_get_message(buf, &buflen)) // Non-blocking
    {
        digitalWrite(led_pin, HIGH); // Flash a light to show received good message  
        serial_send(buf, buflen);      
        digitalWrite(led_pin, LOW);
    }
    else
    {
        unsigned long time = millis();

        unsigned long pdiff = time - photores_time;
        if (pdiff > 1000)
        {
            photores_time = time;
            int v = analogRead(photo_pin);
            int vdiff = abs(photores_v - v);
            unsigned long sdiff = time - photolastsendtime;
            if (sdiff > 300000 || vdiff > 2)
            {
                buf[0] = 1;buf[1] = 131;buf[2]= seq++; buf[3]=4;buf[4]=0;buf[5]=v & 0xFF; buf[6]=v >> 8;
                buflen = 7;
                serial_send(buf, buflen);  
                photores_v = v;  
                photolastsendtime = time;  
            }
        }


        unsigned long tdiff = time - dht_time;
        if (tdiff > 5000)
        {
            dht_time = time;
            int t = dht.readTemperature(true) * 100;
            int h = dht.readHumidity(true) * 100;
            int tdiff = abs(dht_t - t);
            unsigned long sdiff = time - dht_lastsendtime;
            if (sdiff > 300000 || tdiff > 1)
            {
                buf[0] = 1;buf[1] = 131;buf[2]= seq++; buf[3]=5;buf[4]=0;buf[5]=t & 0xFF; buf[6]=t >> 8;buf[7]=h & 0xFF; buf[8]=h >> 8;
                buflen = 9;
                serial_send(buf, buflen);  
                dht_t = t;  
                dht_lastsendtime = time;  
            }
        }
    }
}
