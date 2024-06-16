# Domoticz-Renault-Plugin

A domoticz python plugin for the My Renault API

Please provide feedback about functionality and bugs

## Ideas:

- Allow charging controlled by this plugin
- Something with the location API
- When solar power is high, charge (do some anti ping pong)
- ... your idea here, open an issue for it

### How to charge idea:
- Whenever someone leaves a place where they were charging the car goes to unplugged (maybe not if you replug within the refresh)
- whenever the car changes to unplugged, apply always charging, it won't matter anyway
- whenever getting a plugged state again, evaluate distance
- if distance=home then apply the home switch button to use schedule or always charging
- if distance=away, stay on always charging. or apply a second button... don't enable that one by default
- if the home switch button is toggled, then evaluate if still home and still plugged and apply it

## install
see https://www.domoticz.com/wiki/Using_Python_plugins  
uses https://github.com/hacf-fr/renault-api as set in requirements.txt 

## history

#### 0.2.8 fix of chargemode encoding
- variable names of chargemode reading have changed
- hvac encoding was reverted

#### 0.2.7 encoding of HVAC control
- when renault messed around with hvac encoding as int instead of str

#### 0.2.6 better exception handling
- handle bad login situation
- reorder API calls for better view on debug output

#### 0.2.5 introduction of HVAC control
- on captur, only switch-on works, switch-off is ignored
- update refresh button states so log knows when it was used

#### 0.2.4 split of onStart in create and calling update straight after
- implies a possible action is applied at startup already
- no need to duplicate code
- no other changes

#### 0.2.3 added RefreshNow button
- added some more exception handling
- also cleaned geopy since not in favor of address detection concept

#### 0.2.2 charge strategy implemented as described in README
- only send action command in case there is a delta
- Car Home is at less than 50m from Domoticz Home

#### 0.2.1 introduction of class Action
- cleaner control over actions
- in preparation of business logic updates

#### 0.2.0 based on collected state, able to order an action
- make stateDevice the last in line so it can combine other device values to decide on charging etc.
- renamed stuff to fit better with the plan
- overload exception detection (still need to do something with it though)
- clean out some unused stuff

#### 0.1.9 Distance from home device
- flat earth calculation of distance from home

#### 0.1.8 ChargeIt button
- toggles between Always and Scheduled charging
- status is now an alert and colors reflect plug and charging states

#### 0.1.7 distance from home concept
- and some small stuff

#### 0.1.6 Status-device + Switch-device foundations
- Status shows plugState, chargeStatus and scheduled or always charging
- Switch will toggle between scheduled and always charging
- Switch mechanism is early stages, commands have been tested
- renamed all mileage to distance

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
