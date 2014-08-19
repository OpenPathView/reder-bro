//GoPro Arduino control
#define GOPRO_TRIG      2
#define GOPRO_ID1       {7,8,9,10,11,12}
#define GOPRO_ID2       3
#define GOPRO_ID3       4
#define POW_MOD_1       13
#define POW_MOD_2       6
#define TIME_OUT        2000

void GoPro_powerOn(){            //turn GoPro on
    digitalWrite(POW_MOD_1, LOW);
    digitalWrite(POW_MOD_2, LOW);
    
    delay(350);
    digitalWrite(POW_MOD_1, HIGH);    
    digitalWrite(POW_MOD_2, HIGH);
    delay(4500); //Booting time
    Serial.println("ON");    
}

void GoPro_setMode(){            //turn GoPro in photo mode
    digitalWrite(POW_MOD_1, LOW);
    digitalWrite(POW_MOD_2, LOW);
    
    delay(350);
    digitalWrite(POW_MOD_1, HIGH);    
    digitalWrite(POW_MOD_2, HIGH);
    delay(350); //Security time
    Serial.println("PHOTO_MODE");    
}


void GoPro_powerOff(){          //turn GoPro off
    digitalWrite(POW_MOD_1, LOW);
    digitalWrite(POW_MOD_2, LOW);
    delay(3000);
    digitalWrite(POW_MOD_1, HIGH);
    digitalWrite(POW_MOD_2, HIGH);
    Serial.println("OFF");
}


void GoPro_takePic(){                //take picture
  
    int pinList[] = GOPRO_ID1; //get the pin list
    int start_n[6];            //list of pin initial stat
    for (int i = 0;i<6;i++){
      start_n[i] = digitalRead(pinList[i]);
    }

    digitalWrite(GOPRO_ID2, LOW);
    delayMicroseconds(340);    
    digitalWrite(GOPRO_ID2, HIGH);
    Serial.println("ID2");
    unsigned long time = millis();
    bool notOkList[6];
    int notOk = 1;            //check if all statu are differente == ready
    while (notOk==1){
     notOk = 0;
     for (int i = 0;i<6;i++){
        if(digitalRead(pinList[i]) == start_n[i]){
          notOk = 1;
          notOkList[i]=1;
        }
        else{
          notOkList[i]=0;
        }
        if( (millis()-time)>=TIME_OUT){
          Serial.println("ERROR");
          for (int i = 0;i<6;i++){Serial.print(notOkList[i]);}
          Serial.println("");
          notOk = -1;
          break;          
        }
      }       
    }
    Serial.println("ID1s");    
    digitalWrite(GOPRO_TRIG, LOW); //take pic
    delayMicroseconds(340);
    digitalWrite(GOPRO_TRIG, HIGH);
    Serial.println("TAKEN");
} 

void setup() {
    // Serial output
//    Serial.begin(38400);

    pinMode(POW_MOD_1, OUTPUT);
    digitalWrite(POW_MOD_1, LOW);
    
    pinMode(POW_MOD_2, OUTPUT);
    digitalWrite(POW_MOD_2, LOW);
    
    Serial.begin(9600);
    Serial.println("OFF");
  
    int pinList[] = GOPRO_ID1;  //init all ID1
    for (int i = 0;i<=6;i++){
      pinMode(pinList[i], INPUT);
    }
    
    
    pinMode(GOPRO_ID2, OUTPUT);
    pinMode(GOPRO_ID3, OUTPUT);
    pinMode(GOPRO_TRIG, OUTPUT);
    // 1 photo taken
    
    // Set output lines to their default state
    digitalWrite(GOPRO_TRIG, HIGH);
    digitalWrite(GOPRO_ID2, HIGH);
    digitalWrite(GOPRO_ID3, LOW);     
    
/*    Serial.println("press any key once the camera is in photo mode");
    while (Serial.available() == 0) {}
    Serial.read();
*/
    // ID3 High to say we are going to control the camera, set this low when finished controlling the camera
    digitalWrite(GOPRO_ID3, HIGH); //May take a photo
    
    delay(1500);
//    Serial.println("Begining to take photos");
    
}

void loop() {

  int availableData = 0;
  char lastChar;
  if (Serial.available()>0){
    availableData = Serial.available();
    for (int i = 0; i<availableData;i++){
      lastChar = Serial.read();          
    }
    if (lastChar == 'I'){
      GoPro_powerOn();
    }
    else if(lastChar == 'O'){
      GoPro_powerOff();
    }
    else if(lastChar == 'T'){
      GoPro_takePic();
    }
    else if(lastChar == 'M'){
      GoPro_setMode();
    }    
    else{
      Serial.println("Error");
    }
  }

}
