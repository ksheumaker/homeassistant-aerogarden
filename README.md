# homeassistant-aerogarden
This is a custom component for [Home Assistant](http://home-assistant.io) that adds support for the Miracle Grow [AeroGarden](http://www.aerogarden.com) Wifi hydroponic gardens.

## Background
This was done without help from the AeroGarden people. As far as I can tell they post no public API. I took inspiration and code from the code in this [forum post by epotex](https://community.home-assistant.io/t/first-timer-trying-to-convert-a-working-script-to-create-support-for-a-new-platform).

Currently, the code is setup to query the AeroGarden servers every 30 seconds.

## Tested Models

* Harvest Wifi

(I expect other models to work, since this queries their cloud service not the garden directly)

## Setup
Copy contents of the custom_components/ directory into your <HA-CONFIG>/custom_components directory (```/config/custom_components``` on hassio)

Your directory structure should look like this:
```
   config/custom_components/aerogarden.py
   config/custom_components/binary_sensor/aerogarden.py
   config/custom_components/sensor/aerogarden.py
```
## Configuration
Add the following snippet into your ```configuration.yaml```  replace [EMAIL] and [PASSWORD] with the account information you use in the AeroGarden phone app.

```

aerogarden:
    username: [EMAIL]
    password: [PASSWORD]

```

## Data available
The component supports multiple gardens and multiple sensors will be created for each garden.  [GARDEN NAME] will be replaced by whatever you named the garden in the phone app.
  
### Binary Sensors (on/off) 
* binary_sensor.aerogarden_[GARDEN NAME]_light
* binary_sensor.aerogarden_[GARDEN NAME]_pump
* binary_sensor.aerogarden_[GARDEN NAME]_need_nutrients
* binary_sensor.aerogarden_[GARDEN NAME]_need_water
  
### Sensors
* sensor.aerogarden_[GARDEN NAME]_nutrient
* sensor.aerogarden_[GARDEN NAME]_planted
  
## TODO
1. Code cleanup, this is my first HA component - it probably needs some work.
1. Figure out the API call to turn on/off the light and change it to a light component from a binary_sensor

