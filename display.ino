#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 20, 4);

void setup() {
  Serial.begin(9600);  // Initialize Serial communication
  lcd.init();          // Initialize the LCD
  lcd.backlight();     // Turn on the backlight
  lcd.setCursor(0, 0); // Set the cursor to the current line
  lcd.print("*"); // Display the part
  delay(200);  // Delay for 3000 milliseconds (3 seconds)
  lcd.clear();   // Clear the LCD screen after 3 seconds
}

void loop() {
  if (Serial.available() > 0) { // Check if data is available on the Serial port
    //lcd.clear(); // Clear the LCD
    String receivedMessage = Serial.readStringUntil('\n'); // Read the incoming message
    
    // Split the message by "|"
    String parts[4]; // Assuming there are up to 4 parts separated by "|"
    int partCount = splitString(receivedMessage, '|', parts, 4);
    
    String trimmedPart = parts[0];
    //trimmedPart.trim();
    
    if (trimmedPart.indexOf("   Welcome to WJV   ") == -1) {
      lcd.clear();
    }




    // Display each part on a separate line
    for (int i = 0; i < partCount; i++) {
      lcd.setCursor(0, i); // Set the cursor to the current line
      lcd.print(parts[i]); // Display the part
    }
  }
}

int splitString(String input, char separator, String parts[], int maxParts) {
  int partCount = 0;
  int startIndex = 0;
  int endIndex = input.indexOf(separator);

  while (endIndex >= 0 && partCount < maxParts) {
    parts[partCount] = input.substring(startIndex, endIndex);
    startIndex = endIndex + 1;
    endIndex = input.indexOf(separator, startIndex);
    partCount++;
  }

  // Add the last part (after the final separator)
  if (partCount < maxParts) {
    parts[partCount] = input.substring(startIndex);
    partCount++;
  }

  return partCount;
}
