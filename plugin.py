# Copyright (C) 2023 HomeACcessoryKid
#
# This software is licensed as described in the file LICENSE, which
# you should have received as part of this distribution.
#
# Domoticz-Renault-Plugin   ( https://github.com/HomeACcessoryKid/Domoticz-Renault-Plugin )
#
# Heavily inspired by https://github.com/joro75/Domoticz-Toyota-Plugin
# Many thanks to John de Rooij!
"""
<plugin key="Renault" name="Renault" author="HomeACcessoryKid" version="0.1.2"
        externallink="https://github.com/HomeACcessoryKid/Domoticz-Renault-Plugin">
    <description>
        <h2>Domoticz Renault Plugin 0.1.2</h2>
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
            <li>Mileage - Shows the daily and total mileage of the car</li>
            <li>Fuel level - Shows the current fuel level percentage</li>
            <li>Charge - Shows the charges made and the energy increase</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Username - The username that is also used to login in the MyRenault application.</li>
            <li>Password - The password that is also used to login in the MyRenault application.</li>
            <li>Car - The License plate or VIN for the car for which the data should be retrieved.</li>
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
        <param field="Mode2" label="Language_Country" width="150px">
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
from typing import Any, Union, List, Tuple, Optional, Dict
import arrow

REFRESH_RATE: int = 10

MINIMUM_PYTHON_VERSION = (3, 8)
MINIMUM_MYRENAULT_VERSION: str = '0.2.0'
# MINIMUM_GEOPY_VERSION: str = '2.3.0'
# NOMINATIM_USER_AGENT = 'Domoticz-Renault-Plugin'

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

# try:
#     import geopy.distance
#     geopy_version = Version(geopy.__version__)
#     if geopy_version < Version(MINIMUM_GEOPY_VERSION):
#         _importErrors += ['The geopy version is too old, an update is needed.']
#         del geopy
#         del sys.modules['geopy']
# 
#     if 'geopy' in sys.modules:
#         from geopy.geocoders import Nominatim
# except (ModuleNotFoundError, ImportError):
#     _importErrors += ['The python geopy library is not installed.']


UNIT_MILEAGE_INDEX: int = 1
UNIT_FUEL_INDEX:    int = 2
UNIT_CHARGE_INDEX:  int = 3

class ReducedHeartBeat(ABC):
    """Helper class that only calls the update of the devices just before the hour or midnight"""

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
    def update_devices(self) -> None:
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
            except renault_api.exceptions.RenaultException as ex:
                Domoticz.Error(f'Login Failed: {ex}')
            if self._logged_on:
                Domoticz.Log('Succesfully logged on')
                cars=await account.get_vehicles()
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


    async def _retrieve_status(self) -> Union[Any, None]:
        """Get status from the Renault MyR servers."""
        Domoticz.Debug('_retrieve_status')
        now = datetime.datetime.now()
        async with aiohttp.ClientSession() as websession:
            try:
                client = RenaultClient(websession=websession, locale=Parameters['Mode2'])
                await client.session.login(Parameters['Username'], Parameters['Password'])
                account = await  client.get_api_account(self._accountId)
                vehicle = await account.get_api_vehicle(self._car.vehicleDetails.vin)
                vehicle_status = await asyncio.gather(
                    *[
                        vehicle.get_cockpit(),        # [0] fuelAutonomy fuelQuantity totalMileage
                        vehicle.get_charges(now,now), # [1] charges of today
                        vehicle.get_charge_mode(),    # [2] chargeMode
                        #vehicle.get_battery_status(), # [3] timestamp batteryLevel batteryAutonomy plugStatus chargingStatus
                        #vehicle.get_location(),       # [4] gpsLongitude gpsLatitude lastUpdateTime gpsDirection
                    ]
                )
                return vehicle_status
            except renault_api.exceptions.RenaultException as ex:
                Domoticz.Error(f'Retrieve Error: {ex}')
                self._logged_on = False
                return None


    def retrieve_vehicle_status(self) -> Union[Any, None]:
        """Retrieve and return the status information of the vehicle."""
        vehicle_status = None
        if not self._logged_on:
            asyncio.run(self._connect_to_myr())
        if self._logged_on:
            Domoticz.Log('Updating vehicle status')
            vehicle_status = asyncio.run(self._retrieve_status())
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
    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        return

    def update(self, vehicle_status) -> None:
        """
        Determine the actual value of the instrument and
        update the device in Domoticz.
        """
        return

class MileageRenaultDevice(RenaultDomoticzDevice):
    """The Domoticz device that shows the mileage."""

    def __init__(self) -> None:
        super().__init__(UNIT_MILEAGE_INDEX)
        self._last_mileage: int = 0

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Device(Name='Distance', Unit=self._unit_index,
                                Type=113, Switchtype=3,
                                Used=1,
                                Description='Counter to hold the overall distance',
                                Options={'ValueQuantity': 'Distance',
                                         'ValueUnits': 'km',
                                        }
                                ).Create()

        # Retrieve the last mileage that is already known in Domoticz
        if self.exists():
            try:
                self._last_mileage = int(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_mileage = 0

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                mileage = vehicle_status[0].totalMileage
                diff = mileage - self._last_mileage
                if diff >= 0 or self.requires_update(): # Mileage can only go up
                    Devices[self._unit_index].Update(nValue=0, sValue=f'{mileage}')
                    self._last_mileage = mileage
                    self.did_update()


class FuelRenaultDevice(RenaultDomoticzDevice):
    """The Domoticz device that shows the fuel level percentage."""

    def __init__(self) -> None:
        super().__init__(UNIT_FUEL_INDEX)
        self._last_fuel: float = 0.0

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status:
            if not self.exists():
                Domoticz.Device(Name='Fuel level', Unit=self._unit_index,
                                TypeName='Percentage',
                                Used=1,
                                Image=10, # LogFire (represents fossile fuel)
                                Description='The filled percentage of the fuel tank'
                                ).Create()

        if self.exists():
            try:
                self._last_fuel = float(Devices[self._unit_index].sValue)
            except ValueError:
                self._last_fuel = 0

    def update(self, vehicle_status) -> None:
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

    def create(self, vehicle_status) -> None:
        """Check if the device is present in Domoticz, and otherwise create it."""
        if vehicle_status:
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

    def update(self, vehicle_status) -> None:
        """Determine the actual value of the instrument and update the device in Domoticz."""
        if vehicle_status:
            if self.exists():
                old_day_date=''
                rd=vehicle_status[1].raw_data
                now = datetime.datetime.now()
                sValn='-1;0;' + now.strftime('%Y-%m-%d') + ' 00:00:00'
                Devices[self._unit_index].Update(nValue=0,sValue=sValn)  # register a zero point at 00:00
                for charge in rd['charges']:
                    energy=round(charge['chargeEnergyRecovered']*1000)
                    day_date=charge['chargeStartDate'][0:10]
                    day_time=charge['chargeStartDate'][11:19] # TODO: take TZ and DST into account
                    if day_date == old_day_date:
                        daytotal+=energy
                    else:
                        daytotal=energy
                    old_day_date = day_date
                    sValh='-1;' + str(energy)   + ';' + day_date + ' ' + day_time
                    sVald='-1;' + str(daytotal) + ';' + day_date
                    Devices[self._unit_index].Update(nValue=0,sValue=sValh)
                    Devices[self._unit_index].Update(nValue=0,sValue=sVald)
                self.did_update()


class RenaultPlugin(ReducedHeartBeat, MyRenaultConnector):
    """Domoticz plugin function implementation to get information from MyRenault."""

    def __init__(self) -> None:
        super().__init__()
        self._devices: List[RenaultDomoticzDevice] = []
        self._now = arrow.now()

    def add_devices(self) -> None:
        """Add all the device classes that are part of this plugin."""
        self._devices += [MileageRenaultDevice()]
        self._devices += [FuelRenaultDevice()]
        self._devices += [ChargeRenaultDevice()]

    def create_devices(self) -> None:
        """Create the appropiate devices in Domoticz for the vehicle."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for device in self._devices:
                device.create(vehicle_status)
                device.update(vehicle_status)

    def update_devices(self) -> None:
        """Retrieve the status of the vehicle and update the Domoticz devices."""
        vehicle_status = self.retrieve_vehicle_status()
        if vehicle_status:
            for device in self._devices:
                device.update(vehicle_status)


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

def onStop() -> None:
    """Callback from Domoticz that the plugin is stopped."""
    if _plugin:
        _plugin.disconnect()

def onHeartbeat() -> None:
    """Callback from Domoticz that the plugin can perform some work."""
    if _plugin:
        _plugin.onHeartbeat()

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
