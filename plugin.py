# Copyright (C) 2023-2024 HomeACcessoryKid
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#
# Domoticz-Renault-Plugin   ( https://github.com/HomeACcessoryKid/Domoticz-Renault-Plugin )
#
# Heavily inspired by https://github.com/joro75/Domoticz-Toyota-Plugin
# Many thanks to John de Rooij!
"""
<plugin key="Renault" name="Renault" author="HomeACcessoryKid" version="0.2.8"
        externallink="https://github.com/HomeACcessoryKid/Domoticz-Renault-Plugin">
    <description>
        <h2>Domoticz Renault Plugin 0.2.8</h2>
        <ul style="list-style-type:none">
            <li>A Domoticz plugin that provides devices for a Renault car with connected services.</li>
            <li>It is using the same API that is used by the MyRenault connected service.</li>
        </ul>
        <ul style="list-style-type:none">
            <li>The car should first be made available in the MyRenault connected services,</li>
            <li>after which this plugin can retrieve the information,</li>
            <li>which is then provided as several devices in Domoticz.</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Distance - Shows the daily and total distance of the car</li>
            <li>Fuel level - Shows the current fuel level percentage</li>
            <li>Charge - Shows the charges made and the energy increase</li>
            <li>ChargingStatus - Shows plugState, chargingStatus and if Scheduled or Always charging</li>
            <li>ChargeNowWhenAtHome - Toggle between Scheduled and Always charging, when at Home</li>
            <li>Distance to Home - How far away is your car from home in a straight line.</li>
            <li>Airco/Heater - start Airco/Heater (stop does not work on Captur, must start car for that!)</li>
            <li>RefreshNow - Update all sensors</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the MyRenault app.</li>
            <li>Password - The password that is also used to login in the MyRenault app.</li>
            <li>Car -      The License plate or VIN if more than one car is available.</li>
            <li>Locale -   The language and country that apply to your car</li>
        </ul>
        <h4>Domoticz issue</h4>
        <ul style="list-style-type:none">
            <li>When Updating the configuration, Domoticz' Python interpreter crashes.</li>
            <li>Please restart Domoticz via command line with 'sudo service domoticz restart'.</li>
            <li>See https://github.com/domoticz/domoticz/issues/5717 for hints.</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Username" width="200px" required="true"/>
        <param field="Password" label="Password" width="200px" required="true" password="true"/>
        <param field="Mode1" label="Car" width="200px" required="false" />
        <param field="Mode2" label="Locale" width="150px">
            <options>
                <option label="nl_NL" value="nl_NL"  default="true" />
                <option label="bg_BG" value="bg_BG"/>
                <option label="cs_CZ" value="cs_CZ"/>
                <option label="da_DK" value="da_DK"/>
                <option label="de_DE" value="de_DE"/>
                <option label="de_AT" value="de_AT"/>
                <option label="de_CH" value="de_CH"/>
                <option label="en_GB" value="en_GB"/>
                <option label="en_IE" value="en_IE"/>
                <option label="es_ES" value="es_ES"/>
                <option label="es_MX" value="es_MX"/>
                <option label="fi_FI" value="fi_FI"/>
                <option label="fr_FR" value="fr_FR"/>
                <option label="fr_BE" value="fr_BE"/>
                <option label="fr_CH" value="fr_CH"/>
                <option label="fr_LU" value="fr_LU"/>
                <option label="hr_HR" value="hr_HR"/>
                <option label="hu_HU" value="hu_HU"/>
                <option label="it_IT" value="it_IT"/>
                <option label="it_CH" value="it_CH"/>
                <option label="nl_BE" value="nl_BE"/>
                <option label="no_NO" value="no_NO"/>
                <option label="pl_PL" value="pl_PL"/>
                <option label="pt_PT" value="pt_PT"/>
                <option label="ro_RO" value="ro_RO"/>
                <option label="ru_RU" value="ru_RU"/>
                <option label="sk_SK" value="sk_SK"/>
                <option label="sl_SI" value="sl_SI"/>
                <option label="sv_SE" value="sv_SE"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import sys
from abc import ABC, abstractmethod
import asyncio
import aiohttp
import datetime
from zoneinfo import ZoneInfo
from typing import Any, Union, List, Tuple, Optional, Dict
import math # for cosine of Latitude to do distance calculation to home
from enum import Flag

REFRESH_RATE: int = 10

MINIMUM_PYTHON_VERSION = (3, 8)
MINIMUM_MYRENAULT_VERSION: str = '0.2.0'

_importErrors = []

try:
    import Domoticz
except (ModuleNotFoundError, ImportError):
    _importErrors += [('The Python Domoticz library is not installed. '
                       'This plugin can only be used in Domoticz. '
                       'Check your Domoticz installation')]

try:
    from Domoticz import Parameters, Devices, Settings, Images
except (ModuleNotFoundError, ImportError):
    pass

# try:
#     import setuptools
#     Version = setuptools.distutils.version.LooseVersion
# except (ModuleNotFoundError, ImportError):
#     _importErrors += ['The python setuptools library is not installed.']

try:
    import renault_api  # type: ignore

#     try:
#         renault_api_version = Version(renault_api.__version__)
#         if renault_api_version < Version(MINIMUM_MYRENAULT_VERSION):
#             _importErrors += ['The renault_api version is too old, an update is needed.']
#             del renault_api
#             del sys.modules['renault_api']
#     except AttributeError:
#         _importErrors += ['The renault_api version is too old, an update is needed.']

    if 'renault_api' in sys.modules:
        from renault_api.renault_client import RenaultClient
#         import renault_api.kamereon.exceptions
#         import renault_api.gigya.exceptions
except (ModuleNotFoundError, ImportError):
    _importErrors += ['The Python renault_api library is not installed.']


UNIT_DISTANCE_INDEX:    int = 1
UNIT_FUEL_INDEX:        int = 2
UNIT_CHARGE_INDEX:      int = 3
UNIT_SWITCH_INDEX:      int = 4
UNIT_STATUS_INDEX:      int = 5
UNIT_SEPARATION_INDEX:  int = 6
UNIT_REFRESH_INDEX:     int = 7
UNIT_AIRCO_INDEX:       int = 8

class Action(Flag):
    NO_ACTION        = 0
    CHARGE_ALWAYS    = 1
    CHARGE_SCHEDULED = 2
    CHARGE           = CHARGE_ALWAYS | CHARGE_SCHEDULED
    AC_ON            = 4
    AC_OFF           = 8
    
    def api_cmd(self):
        cmd={ self.CHARGE_ALWAYS:   "always_charging",
              self.CHARGE_SCHEDULED:"schedule_mode",
              self.AC_ON:           "",
              self.AC_OFF:          ""}
        return cmd[self]
        
    def api_res(self):
        res={ self.CHARGE_ALWAYS:   "always_charging",
              self.CHARGE_SCHEDULED:"schedule_mode",
              self.AC_ON:           "on",
              self.AC_OFF:          "off"}
        return res[self]

class ReducedHeartBeat(ABC):
    """Helper class that only calls the update of the devices just before a specific multiple of minutes"""

    def __init__(self) -> None:
        super().__init__()
        self._last_update = datetime.datetime.now()

    def onHeartbeat(self) -> None:
        """Callback from Domoticz that the plugin can perform some work."""
        now = datetime.datetime.now()
        diff = now - self._last_update                   #prevent slip hit twice in 10s or skipping a beat
        if now.minute%REFRESH_RATE == REFRESH_RATE-1 and now.second > 39 and now.second < 51 and diff.seconds > 13:
            self._last_update = now
            self.update_devices()
            

    @abstractmethod
    def update_devices(self, action: Action) -> None:
        """Retrieve the status of the device and update the Domoticz devices."""
        return

class MyRenaultConnector():
    """Provide a connection to the MyRenault service."""

    def __init__(self) -> None:
        super().__init__()
        self._logged_on = False
        self._car: Optional[Dict[str, Any]] = None
        self._accountId = None

    def _lookup_car(self, cars: Optional[List[Dict[str, Any]]],
                identifier: str) -> Optional[Dict[str, Any]]:
        """Find and return the first car from cars that confirms to the passed identifier."""
        if not cars is None and identifier:
            car_id = identifier.upper().strip()
            for car in cars:
                if car_id in car.vehicleDetails.vin.upper():
                    return car
                if car_id in car.vehicleDetails.registrationNumber.upper():
                    return car
        return None


    async def _connect_to_myr(self) -> None:
        """Connect to the Renault MyR servers."""
        Domoticz.Debug('_connect_to_myr')
        self._logged_on = False
        cars: Optional[List[Any]] = None
        async with aiohttp.ClientSession() as websession:
            try:
                client = RenaultClient(websession=websession, locale=Parameters['Mode2'])
                await client.session.login(Parameters['Username'], Parameters['Password'])
                person=await client.get_person()
                for accnt in person.accounts:
                    if accnt.accountType=='MYRENAULT':
                        self._accountId=accnt.accountId
                Domoticz.Status('Using accountID: ' + self._accountId)
                account = await client.get_api_account(self._accountId)
                self._logged_on = True
            except (aiohttp.client_exceptions.ClientResponseError,
                    renault_api.exceptions.RenaultException) as ex:
                Domoticz.Error(f'Login Failed: {ex}')
            if self._logged_on:
                Domoticz.Log('Succesfully logged on')
                cars=await account.get_vehicles()
                if cars.errors is None and not cars.vehicleLinks is None:
                    if len(cars.vehicleLinks) == 1:
                        self._car = cars.vehicleLinks[0]
                    else:
                        self._car = self._lookup_car(cars.vehicleLinks, Parameters['Mode1'])
                        if self._car is None:
                            self._car = self._lookup_car(cars.vehicleLinks, Parameters['Name'])
                    if self._car is None:
                        self._logged_on = False
                        Domoticz.Error('Could not find the desired car: choose one from the below list')
                        for car in cars.vehicleLinks:
                            Domoticz.Error( 'VIN: ' + car.vehicleDetails.vin + 
                                           ' LicensePlate: ' + car.vehicleDetails.registrationNumber +
                                           ' Model: ' + car.vehicleDetails.model.label +
                                           ' ' + car.vehicleDetails.engineEnergyType)
                    else:
                        Domoticz.Status('Using VIN: ' + self._car.vehicleDetails.vin + 
                                       ' LicensePlate: ' + self._car.vehicleDetails.registrationNumber +
                                       ' Model: ' + self._car.vehicleDetails.model.label +
                                       ' ' + self._car.vehicleDetails.engineEnergyType)
                else:
                    Domoticz.Error('Error in get_vehicles:' + cars)


    async def _engage_vehicle(self, action: Action) -> Union[Any, None]:
        """Get status from the Renault MyR servers."""
        Domoticz.Debug('_engage_vehicle ' + action.name)
        now = datetime.datetime.now()
        attempt = 3
        while attempt:
            try:
                async with aiohttp.ClientSession() as websession:
                    client = RenaultClient(websession=websession, locale=Parameters['Mode2'])
                    await client.session.login(Parameters['Username'], Parameters['Password'])
                    account = await  client.get_api_account(self._accountId)
                    vehicle = await account.get_api_vehicle(self._car.vehicleDetails.vin)
                    if action: # zero is reserved for no action, just collect vehicle_status
                        if action in Action.CHARGE:
                            pending = 3
                            while pending:
                                result = await vehicle.get_charge_mode()
                                if result.chargeMode == action.api_res():
                                    pending = 0
                                else:
                                    Domoticz.Status(await vehicle.set_charge_mode(action.api_cmd()))
                                    await asyncio.sleep(3)
                                    pending -= 1
                        if action in Action.AC_ON:
                            pending = 3
                            while pending:
                                result = await vehicle.get_hvac_status()
                                if result.hvacStatus == action.api_res():
                                    pending = 0
                                else:
                                    Domoticz.Status(await vehicle.set_ac_start(20.0)) # TODO: make temperature a parameter
                                    await asyncio.sleep(3)
                                    pending -= 1
                        if action in Action.AC_OFF:
                            pending = 3
                            while pending:
                                result = await vehicle.get_hvac_status()
                                if result.hvacStatus == action.api_res():
                                    pending = 0
                                else:
                                    Domoticz.Status(await vehicle.set_ac_stop())
                                    await asyncio.sleep(3)
                                    pending -= 1
                    vehicle_status = []
                    vehicle_status.append(await vehicle.get_cockpit())        #[0] fuelAutonomy fuelQuantity totalMileage
                    vehicle_status.append(await vehicle.get_charge_mode())    #[1] chargeMode
                    vehicle_status.append(await vehicle.get_battery_status()) #[2] timestamp batteryLevel batteryAutonomy plugStatus chargingStatus
                    vehicle_status.append(await vehicle.get_location())       #[3] timestamp gpsLongitude gpsLatitude lastUpdateTime gpsDirection
                    vehicle_status.append(await vehicle.get_hvac_status())    #[4] hvacStatus socThreshold internalTemperature lastUpdateTime
                    vehicle_status.append(await vehicle.get_charges(now,now)) #[5] charges of today
#                     vehicle_status.append(await vehicle.get_details())
#                     vehicle_status.append(await vehicle.get_charging_settings())
#                     vehicle_status.append(await vehicle.get_hvac_settings())
                    #vehicle_status.append(await vehicle.get_lock_status())                  #broken
                    #vehicle_status.append(await vehicle.get_notification_settings())        #broken
                    #vehicle_status.append(await vehicle.get_res_state())                    #broken
                    #vehicle_status.append(await vehicle.get_hvac_sessions(now,now))         #broken
                    return vehicle_status
            except (aiohttp.client_exceptions.ClientResponseError,
                    aiohttp.client_exceptions.ClientConnectorError,
                    renault_api.kamereon.exceptions.FailedForwardException) as ex:
                Domoticz.Error(f'Try again? {attempt}: {ex}')
                attempt -= 1
                if attempt:
                    await asyncio.sleep(5)
            except renault_api.kamereon.exceptions.QuotaLimitException as ex:
                Domoticz.Error(f'Overload Error: {ex}')
                attempt = 0
            except renault_api.exceptions.RenaultException as ex:
                Domoticz.Error(f'Retrieve Error: {ex}')
                attempt = 0
        self._logged_on = False
        return None


    def engage_vehicle(self, action: Action = 0) -> Union[Any, None]:
        """Perform action and Retrieve the status information of the vehicle."""
        vehicle_status = None
        if not self._logged_on:
            asyncio.run(self._connect_to_myr())
        if self._logged_on:
            try:
                if not self._car.vehicleDetails.vin is None:
                    Domoticz.Log('Engaging Vehicle')
                    vehicle_status = asyncio.run(self._engage_vehicle(action))
                else:
                    Domoticz.Error('Lost login with no VIN')
                    self._logged_on = False
            except AttributeError as ex:
                Domoticz.Error(f'Lost login: {ex}')
                self._logged_on = False
        if vehicle_status is None:
            Domoticz.Error('Vehicle status could not be retrieved')
        else:
            Domoticz.Log(vehicle_status)
        return vehicle_status


    def disconnect(self) -> None:
        """Disconnect from the MyRenault servers."""
        self._logged_on = False


class DomoticzDevice(ABC):
    """Representation of a generic updateable Domoticz devices."""

    def __init__(self, unit_index: int) -> None:
        super().__init__()
        self._unit_index = unit_index
        self._last_update = datetime.datetime.now()
        self._update_interval = 6 * 3600
        self._do_first_update = True

    def exists(self) -> bool:
        """Check if the Domoticz device is present and existing."""
        return (self._unit_index in Devices) and (Devices[self._unit_index])

    def did_update(self) -> None:
        """Remember that an update of the device is done."""
        self._last_update = datetime.datetime.now()
        self._do_first_update = False

    def requires_update(self) -> bool:
        """Determine if an update of the device is needed."""
        diff = datetime.datetime.now() - self._last_update
        return (diff.seconds > self._update_interval) or self._do_first_update

class RenaultDomoticzDevice(DomoticzDevice):
    """
    A generic updateable Domoticz device, to represent information from
    a MyRenault connected services car.
    """

    @abstractmethod
    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        return

    def update(self, vehicle_status) -> Action: # return: which next action to apply
        """
        Determine the actual value of the instrument and
        update the device in Domoticz.
        """
        return

    def onCommand(self, Command, Level, Color) -> Action: # return: which action to apply
        """
        Process a command for this device and
        update the device in Domoticz.
        """
        return

class SeparationRenaultDevice(RenaultDomoticzDevice):
    """The Domoticz device that shows the distance between the parked car and home."""

    def __init__(self) -> None:
        super().__init__(UNIT_SEPARATION_INDEX)
        self._home: Optional[Tuple[float, ...]] = None
        if Settings['Location']: # we assume the earth is flat and square near the home location
            self._home = tuple(float(part) for part in Settings['Location'].split(';'))
            self._degreev: float=40000/360                                          # kmeters at equator per degree
            self._degreeh=self._degreev*math.cos(float(self._home[0])*math.pi/180)  # kmeters at home Latitude per degree

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='Distance to home', Unit=self._unit_index,
                            TypeName='Custom Sensor', Type=243, Subtype=31,
                            Options={'Custom': '1;km'},
                            Used=1,
                            Description='The distance between home and the car'
                            ).Create()

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                kmetersv=self._degreev*(float(self._home[0])-vehicle_status[3].gpsLatitude)
                kmetersh=self._degreeh*(float(self._home[1])-vehicle_status[3].gpsLongitude)
                dist=round(math.sqrt(kmetersv*kmetersv+kmetersh*kmetersh),3)
                Devices[self._unit_index].Update(nValue=0, sValue=f'{dist}')


class DistanceRenaultDevice(RenaultDomoticzDevice): # TODO: make option for miles based on relevant locale?
    """The Domoticz device that shows the distance."""

    def __init__(self) -> None:
        super().__init__(UNIT_DISTANCE_INDEX)
        self._last_distance: int = 0

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='Distance', Unit=self._unit_index,
                            Type=113, Switchtype=3,
                            Used=1,
                            Description='Counter to hold the overall distance',
                            Options={'ValueQuantity': 'Distance',
                                     'ValueUnits': 'km',
                                    }
                            ).Create()

        # Retrieve the last distance that is already known in Domoticz
        if self.exists():
            try:
                self._last_distance = int(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_distance = 0

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                distance = vehicle_status[0].totalMileage
                diff = distance - self._last_distance
                if diff >= 0 or self.requires_update(): # Distance can only go up
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{distance}')
                    self._last_distance = distance
                    self.did_update()


class FuelRenaultDevice(RenaultDomoticzDevice):
    """The Domoticz device that shows the fuel level percentage."""

    def __init__(self) -> None:
        super().__init__(UNIT_FUEL_INDEX)
        self._last_fuel: float = 0.0

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='Fuel level', Unit=self._unit_index,
                            TypeName='Percentage',
                            Used=1,
                            Image=10, # LogFire (represents Fossil Fuel)
                            Description='The filled percentage of the fuel tank'
                            ).Create()
        if self.exists():
            try:
                self._last_fuel = float(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_fuel = 0

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                fuel = vehicle_status[0].fuelQuantity/0.4 # TODO: make this litres or learn tank volume
#                 if fuel != self._last_fuel or self.requires_update():
                Devices[self._unit_index].Update(nValue=0, sValue=str(fuel))
                self._last_fuel = fuel
                self.did_update()


class ChargeRenaultDevice(RenaultDomoticzDevice):
    """The Domoticz device that shows the charges made"""

    def __init__(self) -> None:
        super().__init__(UNIT_CHARGE_INDEX)
        self._last_fuel: float = 0.0

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='Charge', Unit=self._unit_index,
                            Type=243, Subtype=33, Switchtype=0, # Managed Counter
                            Used=1,
                            Image=1, # Wall Socket (represents Electric Energy)
                            Description='The amount of energy charged'
                            ).Create()
        if self.exists():
            try:
                self._last_fuel = float(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_fuel = 0

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status: # TODO: make a at home and elsewhere counter...
            if self.exists():
                old_csd_date=''
                raw_data=vehicle_status[5].raw_data
                now = datetime.datetime.now()
                sValn='-1;0;' + now.strftime('%Y-%m-%d') + ' 00:00:00'
                Devices[self._unit_index].Update(nValue=0,sValue=sValn)  # register a zero point at 00:00
                for charge in raw_data['charges']:
                    energy=round(charge['chargeEnergyRecovered']*1000)
                    if energy<0: #Renault API is able to report a negative number !!!
                        energy=1 #signal that something bad happened but not significant to disturb
                    ncsd=datetime.datetime.strptime(charge['chargeStartDate'],'%Y-%m-%dT%H:%M:%SZ') #2023-09-17T00:00:49Z
                    ucsd=ncsd.replace(tzinfo=ZoneInfo('UTC'))   #convert naive time to UTC aware
                    lcsd=ucsd.astimezone(ZoneInfo('localtime')) #present in the local timezone
                    csd_time=lcsd.strftime('%Y-%m-%d %H:%M:%S')
                    csd_date=lcsd.strftime('%Y-%m-%d')
                    if csd_date == old_csd_date:
                        daytotal+=energy
                    else:
                        daytotal=energy
                    old_csd_date = csd_date
                    sValt='-1;' + str(energy)   + ';' + csd_time
                    sVald='-1;' + str(daytotal) + ';' + csd_date
                    Devices[self._unit_index].Update(nValue=0,sValue=sValt)
                    Devices[self._unit_index].Update(nValue=0,sValue=sVald)
                self.did_update()


class ChargeRenaultSwitch(RenaultDomoticzDevice):
    """The Domoticz device that enables charges"""

    def __init__(self) -> None:
        super().__init__(UNIT_SWITCH_INDEX)

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='ChargeNowWhenAtHome', Unit=self._unit_index,
                            Type=244, Subtype=73, Switchtype=0, # Switch on/off
                            Description="Toggle between Scheduled and Always charging in case at Home and Plugged in",
                            Used=1
                            ).Create()

    def onCommand(self, Command, Level, Color) -> Action: # return: which action to apply
        """Process a command for this device and update the device in Domoticz."""
        if self.exists():
            if Command == "On":
                Devices[self._unit_index].Update(nValue=1,sValue="")
                return Action.CHARGE_ALWAYS
            if Command == "Off":
                Devices[self._unit_index].Update(nValue=0,sValue="")
                plugged_in = True if Devices[UNIT_STATUS_INDEX].nValue else False # TODO: decide what to do with level 4 Error
                dst_from_home =  Devices[UNIT_SEPARATION_INDEX].sValue
                if plugged_in and float(dst_from_home) < 0.05:  # less than 50m is Home ??
                    return Action.CHARGE_SCHEDULED
                else:
                    return Action.CHARGE_ALWAYS
            return Action.NO_ACTION


class RefreshRenaultSwitch(RenaultDomoticzDevice):
    """The Domoticz device that refreshes readings"""

    def __init__(self) -> None:
        super().__init__(UNIT_REFRESH_INDEX)

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='RefreshNow', Unit=self._unit_index,
                            Type=244, Subtype=73, Switchtype=9, # PushOn
                            Description="Refresh car readings now",
                            Used=1
                            ).Create()

    def onCommand(self, Command, Level, Color) -> Action: # return: which action to apply
        """Process a command for this device and update the device in Domoticz."""
        if self.exists():
            if Command == "On":
                Devices[self._unit_index].Update(nValue=1,sValue="")
                Devices[self._unit_index].Update(nValue=0,sValue="")
                return Action.NO_ACTION


class AircoRenaultSwitch(RenaultDomoticzDevice):
    """The Domoticz device that refreshes readings"""

    def __init__(self) -> None:
        super().__init__(UNIT_AIRCO_INDEX)

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='Airco/Heater', Unit=self._unit_index,
                            Type=244, Subtype=73, Switchtype=0, # Switch on/off
                            Description="Switch the Airco/Heater on or off",
                            Used=1
                            ).Create()

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                if vehicle_status[4].hvacStatus == Action.AC_ON.api_res():
                    Devices[self._unit_index].Update(nValue=1,sValue="")
                else:
                    Devices[self._unit_index].Update(nValue=0,sValue="")

    def onCommand(self, Command, Level, Color) -> Action: # return: which action to apply
        """Process a command for this device and update the device in Domoticz."""
        if self.exists():
            if Command == "On":
                return Action.AC_ON
            if Command == "Off":
                return Action.AC_OFF
            return Action.NO_ACTION


class ChargeRenaultStatus(RenaultDomoticzDevice):
    """The Domoticz device that shows three charging statuses"""

    def __init__(self) -> None:
        super().__init__(UNIT_STATUS_INDEX)

    def create(self) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if not self.exists():
            Domoticz.Device(Name='chargingStatus', Unit=self._unit_index,
                            Type=243, Subtype=22, # Alert
                            Used=1
                            ).Create()

    def update(self, vehicle_status) -> Action:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        # TODO: make this based on the Locale language
        states={0.0:"Not_In_Charge", # values taken from kamereon/enums.py
                0.1:"Waiting_For_A_Planned_Charge",
                0.2:"Charge_Ended",
                0.3:"Waiting_For_Current_Charge",
                0.4:"Energy_Flap_Opened",
                1.0:"Charge_In_Progress",
               -1.0:"Charge_Error",
               -1.1:"Unavailable" 
               }
        plugs ={  0:" - Unplugged - ",
                  1:" - Plugged - ",
                 -1:" - PlugError - ",
        -2147483648:" - PlugUnknown - "
               }
        if vehicle_status:
            if self.exists():
                chargeMode = vehicle_status[1].chargeMode
                plugstatus=vehicle_status[2].plugStatus
                state = vehicle_status[2].chargingStatus
                text = chargeMode
                text+=plugs[plugstatus]
                if state in states:
                    text+=states[state]
                else:
                    text+="Unknown chargingStatus: " + str(state)
                if plugstatus < 0 or state < 0:
                    level = 4
                else:
                    if plugstatus == 0:
                        level = 0
                    else:
                        if state < 1:
                            level = 1
                        else:
                            level = 2
                Devices[self._unit_index].Update(nValue=level, sValue=text)
                action = Action.CHARGE_ALWAYS
                if plugstatus == 1:
                    dst_from_home = Devices[UNIT_SEPARATION_INDEX].sValue
                    if float(dst_from_home) < 0.05:
                        if Devices[UNIT_SWITCH_INDEX].nValue == 0:
                            action = Action.CHARGE_SCHEDULED
                Domoticz.Debug(chargeMode)
                Domoticz.Debug(action.api_res())
                if chargeMode == action.api_res():
                    return Action.NO_ACTION
                else:
                    return action


class RenaultPlugin(ReducedHeartBeat, MyRenaultConnector):
    """Domoticz plugin function implementation to get information from MyRenault."""

    def __init__(self) -> None:
        super().__init__()
        self._devices: List[RenaultDomoticzDevice] = []

    def add_devices(self) -> None:
        """Add all the device classes that are part of this plugin."""
        self._devices += [SeparationRenaultDevice()]
        self._devices += [DistanceRenaultDevice()]
        self._devices += [FuelRenaultDevice()]
        self._devices += [ChargeRenaultDevice()]
        self._devices += [ChargeRenaultSwitch()]
        self._devices += [RefreshRenaultSwitch()]
        self._devices += [AircoRenaultSwitch()]
        self._devices += [ChargeRenaultStatus()]

    def create_devices(self) -> None:
        """Create the appropiate devices in Domoticz for the vehicle."""
        for device in self._devices:
            device.create()

    def update_devices(self, action: Action = Action.NO_ACTION) -> None:
        """Retrieve the status of the vehicle and update the Domoticz devices."""
        turn = 2 # how often engage_vehicle will be called maximum
        next_action = action
        while turn:
            vehicle_status = self.engage_vehicle(next_action)
            next_action = Action.NO_ACTION
            if vehicle_status:
                for device in self._devices:
                    try:
                        next_action = next_action | device.update(vehicle_status)
                    except TypeError: # allows update to not return action explicitly
                        pass
                Domoticz.Status(next_action)
                turn = turn - 1 if next_action else 0
            else:
                turn = 0

    def onCommand(self, Unit, Command, Level, Color) -> None:
        """Process the command"""
        for device in self._devices:
            if Unit == device._unit_index:
                self.update_devices(device.onCommand(Command, Level, Color))


_plugin = RenaultPlugin() if 'renault_api' in sys.modules else None

def onStart() -> None:
    """Callback from Domoticz that the plugin is started."""
    if Parameters["Mode6"] != "0":
        Domoticz.Debugging(int(Parameters["Mode6"]))
        dump_config_to_log()
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        Domoticz.Error(f'Python version {sys.version_info} is not supported,'
                       f' at least {MINIMUM_PYTHON_VERSION} is required.')
    else:
        global _importErrors
        if _importErrors:
            _importErrors += [('Use pip to install required packages: '
                               'pip3 install -r requirements.txt')]
            for err in _importErrors:
                Domoticz.Error(err)
        elif _plugin:
            Domoticz.Debug('onStart start')
            _plugin.add_devices()
            _plugin.create_devices()
            _plugin.update_devices()

def onStop() -> None:
    """Callback from Domoticz that the plugin is stopped."""
    if _plugin:
        _plugin.disconnect()

def onHeartbeat() -> None:
    """Callback from Domoticz that the plugin can perform some work."""
    if _plugin:
        _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Color) -> None:
    """Callback from Domoticz that a command came in."""
    if _plugin:
        _plugin.onCommand(Unit, Command, Level, Color)

def dump_config_to_log() -> None:
    """Dump the configuration of the plugin to the Domoticz debug log."""
    for key in Parameters:
        if Parameters[key] != '':
            value = '******' if key.lower() in ['username', 'password'] else str(Parameters[key])
            Domoticz.Debug(f'\'{key}\': \'{value}\'')
    Domoticz.Debug(f'Device count: {str(len(Devices))}')
    for key in Devices:
        Domoticz.Debug(f'Device:           {str(key)} - {str(Devices[key])}')
        Domoticz.Debug(f'Device ID:       \'{str(Devices[key].ID)}\'')
        Domoticz.Debug(f'Device Name:     \'{Devices[key].Name}\'')
        Domoticz.Debug(f'Device nValue:    {str(Devices[key].nValue)}')
        Domoticz.Debug(f'Device sValue:   \'{Devices[key].sValue}\'')
        Domoticz.Debug(f'Device LastLevel: {str(Devices[key].LastLevel)}')
