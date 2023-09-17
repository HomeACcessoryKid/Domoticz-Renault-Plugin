# Domoticz-Renault-Plugin

A domoticz python plugin for the My Renault API

Second version exposed to the community

Please provide feedback about functionality and bugs

## Ideas:

- Allow charging controlled by this plugin
- Something with the location API
- ... your idea here

## install
see https://www.domoticz.com/wiki/Using_Python_plugins  
uses https://github.com/hacf-fr/renault-api as set in requirements.txt 

## history

#### 0.1.5 single car mode and timezone aware
- when only one car is available, it is chosen automatically
- process charges taking timezone into account

#### 0.1.4 retries and efficiency
- exceptions result in 3 retries
- not using asyncio.gather uses only one TLS session instead of N parallel ones
- verify errors before processing output of account.get_vehicles()
- mark TODO items
- cosmetics

#### 0.1.2 Very first version for public sharing
- Should be working for most people
- Please provide feedback
