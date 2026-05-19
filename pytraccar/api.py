import requests
import json

# --- Import Traccar API Exceptions from your pytraccar.exceptions module ---
from pytraccar.exceptions import (
    TraccarApiException,
    BadRequestException,
    ObjectNotFoundException,
    ForbiddenAccessException,
    InvalidTokenException,
    UserPermissionException
)

# --- YOUR CUSTOM TRACCARAPI CLASS ---
class TraccarAPI:
    """Traccar v6.5 - https://www.traccar.org/api-reference/
    Abstraction for interacting with Traccar REST API.

    """

    def __init__(self, base_url):
        """
        Args:
            base_url: Your traccar server URL.

        Examples:
            TraccarAPI('https://mytraccaserver.com'),
            TraccarAPI('http://1.2.3.4')
        """
        self._token = ''
        self.base_url = base_url # Store base_url for later use in new methods
        self._urls = {
            'devices': base_url + '/api/devices',
            'session': base_url + '/api/session',
            'geofences': base_url + '/api/geofences',
            'notifications': base_url + '/api/notifications',
            'reports_events': base_url + '/api/reports/events', # Keep this for events
            'reports_route': base_url + '/api/reports/route',
            'reports_trips': base_url + '/api/reports/trips',
            'positions': base_url + '/api/positions',
            'users': base_url + '/api/users',
            'groups': base_url + '/api/groups',
            'permissions': base_url + '/api/permissions',
            'commands': base_url + '/api/commands',
            'commands_send': base_url + '/api/commands/send',
            'commands_types': base_url + '/api/commands/types',
        }
        self._session = requests.Session()
        # Storing username and password for basic auth if used
        self.username = None
        self.password = None

    @property
    def token(self):
        """ """
        return self._token

    """
    ----------------------
    /api/session 
    ----------------------
    """
    def login_with_credentials(self, username, password):
        """Path: /session
        Creates a new session with user's credentials.

        Args:
            username: User email
            password: User password

        Returns:
            json: Session info

        Raises:
            ForbiddenAccessException: Wrong username or password.
            TraccarApiException:

        """
        path = self._urls['session']
        data = {'email': username, 'password': password}
        req = self._session.post(url=path, data=data)

        if req.status_code == 200:
            self.username = username # Store username
            self.password = password # Store password
            return req.json()
        elif req.status_code == 401:
            raise ForbiddenAccessException() # Instantiate the exception
        else:
            raise TraccarApiException(info=req.text)

    def login_with_token(self, token):
        """Path: /session
        Creates a new session by using the provided token.

        Args:
          token: User session token.
                 This token can be generated on the web interface.

        Returns:
          json: Session info

        Raises:
          InvalidTokenException:
          TraccarApiException:

        """
        path = self._urls['session']
        data = {'token': token}
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            self._token = token  # Save valid token.
            # When logging in with token, username/password aren't directly available.
            # The session will handle authentication for subsequent calls.
            return req.json()
        elif req.status_code == 404:
            raise InvalidTokenException() # Instantiate the exception
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/devices 
    ----------------------
    """
    def get_all_devices(self):
        """Path: /devices
        Can only be used by admins or managers to fetch all entities.

        Args:

        Returns:
          json: All users devices

        """
        path = self._urls['devices']
        data = {'all': True}
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    def get_devices(self, query=None, params=None):
        """
        Path: /devices
        Fetch a list of devices.
        Without any params, returns a list of the user's devices.

        Args:
          query: Fetch by: userId, id or uniqueId (Default value = None)
          params: identifier or identifiers list.
            Examples: [5, 10], 'myDeviceID' (Default value = None)

        Returns:
          json: Device list

        Raises:
          ObjectNotFoundException:

        """
        path = self._urls['devices']

        if not query:
            req = self._session.get(url=path)
        else:
            data = {query: params}
            req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise ObjectNotFoundException(obj=params, obj_type='Device') # Instantiate with args
        else:
            raise TraccarApiException(info=req.text)

    def create_device(self, name, unique_id, group_id=0,
                      phone='', model='', contact='', category=None, custom_attributes=None):
        """Path: /devices
        Create a device. Only requires name and unique ID.
        Other params are optional.

        https://www.traccar.org/api-reference/#/definitions/Device

        Args:
          name: Device name.
          unique_id: Device unique identifier.
          group_id: Group identifier (Default value = 0)
          phone: Phone number (Default value = None)
          model: Device model (Default value = None)
          contact: (Default value = None)
          category: Device type (Optional)
            Arrow, Default, Animal, Bicycle, Boat, Bus, Car, Crane,
            Helicopter, Motorcycle, Offroad, Person, Pickup, Plane,
            Ship, Tractor, Train, Tram, Trolleybus, Truck, Van
          attributes: {}

        Returns:
          json: Created device.

        Raises:
          BadRequestException: If device exists in database.

        """

        path = self._urls['devices']

        data = {
            "id": -1,  # id auto-assignment
            "name": name,
            "uniqueId": unique_id,
            "phone": phone,
            "model": model,
            "contact": contact,
            "category": category,
            "groupId": group_id,
            "attributes": custom_attributes
        }

        req = self._session.post(url=path, json=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text) # Instantiate with arg
        else:
            raise TraccarApiException(info=req.text)

    def update_device(self, device_id, name=None, unique_id=None, group_id=None,
                      phone=None, model=None, contact=None, category=None, attributes=None,
                      device_info=None):

        if device_info is None:
            # Traccar doesn't support id= filter combined with all=True, so fetch all and find by id
            raw = self._session.get(self._urls['devices'], params={'all': True})
            if raw.status_code != 200:
                raise TraccarApiException(info=raw.text)
            matches = [d for d in raw.json() if d.get('id') == device_id]
            if not matches:
                raise ObjectNotFoundException(obj=device_id, obj_type='Device')
            device_info = matches[0]

        update = {
            'name': name,
            'uniqueId': unique_id,
            'phone': phone,
            'model': model,
            'contact': contact,
            'category': category,
            'groupId': group_id,
            'attributes': attributes
        }

        # Replaces all updated values in device_info
        data = {key: value if update.get(key) is None else update[key] for key, value in device_info.items()}
        headers = {'Content-Type': 'application/json'}

        req = self._session.put('{}/{}'.format(self._urls['devices'], device_id),
                                data=json.dumps(data), headers=headers)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    def delete_device(self, device_id):
        """Path: /devices/{id}
        Delete a device by ID.

        Args:
            device_id: Device identifier.

        Raises:
            TraccarApiException:
        """
        req = self._session.delete('{}/{}'.format(self._urls['devices'], device_id))
        if req.status_code != 204:
            raise TraccarApiException(info=req.text)

    """
        ----------------------
        /api/geofences
        ----------------------
        """

    def get_all_geofences(self):
        """Path: /geofences
        Can only be used by admins or managers to fetch all entities.

        Args:

        Returns:
          json: All geofences

        """
        path = self._urls['geofences']
        data = {'all': True}
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        if req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    def get_geofences(self, query=None, params=None):
        """
        Path: /geofences
        Fetch a list of devices.
        Without any params, returns a list of the user's devices.

        Args:
          query: Fetch by: userId, deviceId, groupId, id (Default value = None)
          params: identifier or identifiers list.
            Examples: [5, 10], 'geoFenceId' (Default value = None)

        Returns:
          json: Geofence list

        Raises:
          ObjectNotFoundException:

        """
        path = self._urls['geofences']

        if not query:
            req = self._session.get(url=path)
        else:
            data = {query: params}
            req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise ObjectNotFoundException(obj=params, obj_type='Geofence')
        else:
            raise TraccarApiException(info=req.text)

    def create_geofence(self, name, area, description='', calendarId=None, attributes=None):
        """Path: /geofences
        Create a geofence. Only requires name and unique ID.
        Other params are optional.

        https://www.traccar.org/api-reference/#/definitions/Geofence

        Args:
          name: Geofence name.
          description: Description
          area: The Geofence area in WKT representation

        Returns:
          json: Created geofence.

        Raises:
          BadRequestException: If Geofence exists in database.

        """

        path = self._urls['geofences']

        data = {
            "id": -1,
            "name": name,
            "description": description,
            "area": str(area),
            "calendarId": calendarId or 0,
            "attributes": attributes or {},
        }

        req = self._session.post(url=path, json=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    def update_geofence(self, geofence_id, name=None, area=None, description=None,
                        calendarId=None, attributes=None):

        # Get current geofence values
        req = self.get_geofences(query='id', params=geofence_id)
        geofence_info = req[0]

        update = {
            'name': name,
            'area': area,
            'description': description,
            'calendarId': calendarId,
            'attributes': attributes,
        }

        # Replaces all updated values in geofence_info
        data = {key: value if update.get(key) is None else update[key] for key, value in geofence_info.items()}
        headers = {'Content-Type': 'application/json'}

        req = self._session.put('{}/{}'.format(self._urls['geofences'], geofence_id),
                                data=json.dumps(data), headers=headers)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    def delete_geofence(self, geofence_id):
        req = self._session.delete('{}/{}'.format(self._urls['geofences'], geofence_id))

        if req.status_code != 204:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/notifications
    ----------------------
    """
    def get_all_notifications(self):
        """Path: /notifications
        Can only be used by admins or managers to fetch all entities

        Args:

        Returns:
          json: list of Notifications

        """
        path = self._urls['notifications']
        data = {'all': True}
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        if req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/reports/events
    ----------------------
    """
    def get_events(self, startTime, endTime, device_ids=None, event_type=None, groupId=None):
        """Path: /reports/events
        Can be used by users to fetch events, including specific types like 'overspeed'.

        Args:
            startTime: Start time (ISO 8601 UTC, e.g., '2019-08-24T14:15:22Z')
            endTime: End time (ISO 8601 UTC, e.g., '2019-08-24T14:15:22Z')
            device_ids: List of device IDs (e.g., ['1', '2']). Optional. If provided, will join into comma-separated string.
                        Note: Traccar's /reports/events 'deviceId' parameter often expects a single ID,
                        so the calling function should iterate if multiple devices are needed for 'deviceOverspeed' type.
            event_type: Specific event type (e.g., 'deviceOverspeed', 'alarm'). Optional.
            groupId: Group ID. Optional.

        Returns:
            json: list of Events

        """
        path = self._urls['reports_events']

        params = {
            'from': startTime,
            'to': endTime,
        }

        # Only add deviceId if it's explicitly provided and not None
        # Note: For 'deviceOverspeed' type, Traccar's API typically expects a single deviceId or groupId.
        # We will prioritize groupId if provided, otherwise device_ids (which will be handled by the caller).
        if groupId is not None:
            params['groupId'] = groupId
        elif device_ids:
            params['deviceId'] = device_ids

        if event_type:
            params['type'] = event_type

        auth_tuple = (self.username, self.password) if self.username and self.password else None
        req = self._session.get(url=path, params=params, auth=auth_tuple)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        elif req.status_code == 401:
            raise ForbiddenAccessException(message="Authentication required or failed for events report.")
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/positions
    ----------------------
    """
    def get_positions(self, deviceId=None, startTime=None, endTime=None, position_id=None):
        """Path: /positions
        Can only be used by users to fetch positions

        Args:

        Returns:
            json: list of Positions
        """
        path = self._urls['positions']
        data = {
            'deviceId': deviceId,
            'from': startTime,
            'to': endTime,
            'id': position_id,
        }
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        if req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/reports/trips
    ----------------------
    """
    def get_trips(self, startTime, endTime, deviceid=None, groupId=None):
        """Path: /reports/trips
        Can be used by users to fetch trip reports.

        Args:
            startTime: Start time (ISO 8601 UTC, e.g., '2019-08-24T14:15:22Z')
            endTime: End time (ISO 8601 UTC, e.g., '2019-08-24T14:15:22Z')
            deviceid: Single device ID (e.g., '1'). Optional.
            groupId: Group ID. Optional.

        Returns:
            json: list of Report Trips

        """
        path = self._urls['reports_trips']
        params = {
            'from': startTime,
            'to': endTime,
        }

        if deviceid is not None:
            params['deviceId'] = str(deviceid)

        if groupId is not None:
            params['groupId'] = str(groupId)

        headers = {'Accept': 'application/json','Content-Type': 'application/json'}
        auth_tuple = (self.username, self.password) if self.username and self.password else None
        req = self._session.get(url=path, params=params, headers=headers, auth=auth_tuple)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        elif req.status_code == 401:
            raise ForbiddenAccessException(message="Authentication required or failed for trips report.")
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/users
    ----------------------
    """
    def get_all_users(self):
        """Path: /users
        Can only be used by admins or managers to fetch all entities.

        Args:

        Returns:
          json: All users
        """
        path = self._urls['users']
        data = {'all': True}
        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        if req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)
    """
    ----------------------
    /api/users
    ----------------------
    """
    def create_user(self, name, email, administrator=False, token=None):
        """Path: /users
        Create a users. Only requires name, email.
        Other params are optional.

        https://www.traccar.org/api-reference/#/definitions/User

        Args:
          name: users name.
          email: Device unique identifier.
          administrator: Group identifier (Default value = 0)
          token: Phone number (Default value = None)

        Returns:
          json: Created user.

        Raises:
          BadRequestException: If user exists in database.

        """

        path = self._urls['users']

        data = {
            "id": -1,  # id auto-assignment
            "name": name,
            "email": email,
            "administrator": administrator,
            "token": token,
            "attributes":{"speedUnit":"kmh"},
        }

        req = self._session.post(url=path, json=data)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)
    """
    ----------------------
    /api/permissions
    ----------------------
    """
    def set_permissions(self, userId, deviceId=0, groupId=0):
        """Path: /permissions
        Can only be used by admins to set positions

        Args:

        Returns:
            json: Permissions object
        """
        path = self._urls['permissions']

        if deviceId != 0:
            data = {"userId": userId, "deviceId": deviceId}
        elif groupId != 0:
            data = {"userId": userId, "groupId": groupId}
        else:
            raise BadRequestException(message="Either deviceId or groupId must be non-zero")

        req = self._session.post(url=path, json=data)

        if req.status_code == 204:
            return data
        if req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/groups
    ----------------------
    """
    def get_groups(self, userId=None):
        """
        Path: /groups
        Fetch a list of groups.
        Without any params, returns a list of the user's groups.

        Args: userId

        Returns:
            json: list of Groups
        """
        path = self._urls['groups']
        data = {
            'userId': userId,
        }

        req = self._session.get(url=path, params=data)

        if req.status_code == 200:
            return req.json()
        if req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/reports/route
    ----------------------
    """
    def get_route(self, deviceid, startTime, endTime):
        """Path: /reports/route
        Can only be used by users to fetch route

        Args:
            deviceid: Device ID
            startTime: Start time (ISO 8601 UTC)
            endTime: End time (ISO 8601 UTC)

        Returns:
            json: list of positions

        """
        path = self._urls['reports_route']
        params = {
            'deviceId': deviceid,
            'from': startTime,
            'to': endTime,
        }

        headers = {'Accept': 'application/json','Content-Type': 'application/json'}
        auth_tuple = (self.username, self.password) if self.username and self.password else None
        req = self._session.get(url=path, params=params, headers=headers, auth=auth_tuple)

        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        elif req.status_code == 401:
            raise ForbiddenAccessException(message="Authentication required or failed for route report.")
        else:
            raise TraccarApiException(info=req.text)

    """
    ----------------------
    /api/commands
    ----------------------
    """
    def get_commands(self, device_id=None, group_id=None, all=False):
        """Path: /commands
        Fetch saved commands. Without params returns commands for the current user.

        Args:
            device_id: Filter by device ID. (Default value = None)
            group_id: Filter by group ID. (Default value = None)
            all: Fetch all entities (admin/manager only). (Default value = False)

        Returns:
            json: List of saved commands.
        """
        path = self._urls['commands']
        params = {}
        if all:
            params['all'] = True
        if device_id is not None:
            params['deviceId'] = device_id
        if group_id is not None:
            params['groupId'] = group_id

        req = self._session.get(url=path, params=params)
        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise UserPermissionException()
        else:
            raise TraccarApiException(info=req.text)

    def create_command(self, device_id, type, description='', text_channel=False, attributes=None):
        """Path: /commands
        Create a saved command.

        Args:
            device_id: Target device ID.
            type: Command type (e.g. 'custom', 'positionSingle', 'positionPeriodic', 'engineStop').
            description: Human-readable label. (Default value = '')
            text_channel: Send via SMS instead of data channel. (Default value = False)
            attributes: Command-specific attributes dict (e.g. {'data': 'msg'} for custom type).

        Returns:
            json: Created command.

        Raises:
            BadRequestException:
        """
        path = self._urls['commands']
        data = {
            "id": -1,
            "deviceId": device_id,
            "type": type,
            "description": description,
            "textChannel": text_channel,
            "attributes": attributes or {},
        }
        req = self._session.post(url=path, json=data)
        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    def update_command(self, command_id, device_id=None, type=None, description=None,
                       text_channel=None, attributes=None):
        """Path: /commands/{id}
        Update a saved command.

        Args:
            command_id: Command identifier.
            device_id: Target device ID.
            type: Command type.
            description: Human-readable label.
            text_channel: Send via SMS.
            attributes: Command-specific attributes.

        Returns:
            json: Updated command.
        """
        req = self._session.get(url=self._urls['commands'])
        if req.status_code != 200:
            raise TraccarApiException(info=req.text)
        matches = [c for c in req.json() if c.get('id') == command_id]
        if not matches:
            raise ObjectNotFoundException(obj=command_id, obj_type='Command')
        command_info = matches[0]

        update = {
            'deviceId': device_id,
            'type': type,
            'description': description,
            'textChannel': text_channel,
            'attributes': attributes,
        }
        data = {key: value if update.get(key) is None else update[key]
                for key, value in command_info.items()}

        req = self._session.put('{}/{}'.format(self._urls['commands'], command_id), json=data)
        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)

    def delete_command(self, command_id):
        """Path: /commands/{id}
        Delete a saved command.

        Args:
            command_id: Command identifier.

        Raises:
            TraccarApiException:
        """
        req = self._session.delete('{}/{}'.format(self._urls['commands'], command_id))
        if req.status_code != 204:
            raise TraccarApiException(info=req.text)

    def send_command(self, device_id, type, text_channel=False, attributes=None):
        """Path: /commands/send
        Dispatch a command to a device immediately, or queue it if not connected.

        Args:
            device_id: Target device ID.
            type: Command type (e.g. 'positionSingle', 'engineStop', 'engineResume', 'custom').
            text_channel: Send via SMS instead of data channel. (Default value = False)
            attributes: Command-specific attributes (e.g. {'data': 'text'} for 'custom').

        Returns:
            json: Dispatched command object.

        Raises:
            BadRequestException: Device not found or command not supported.
            ForbiddenAccessException: Insufficient permissions.
        """
        path = self._urls['commands_send']
        data = {
            "id": -1,
            "deviceId": device_id,
            "type": type,
            "textChannel": text_channel,
            "attributes": attributes or {},
        }
        req = self._session.post(url=path, json=data)
        if req.status_code == 200:
            return req.json()
        elif req.status_code == 202:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        elif req.status_code == 401:
            raise ForbiddenAccessException()
        else:
            raise TraccarApiException(info=req.text)

    def get_command_types(self, device_id=None):
        """Path: /commands/types
        Fetch the list of available command types for a device.
        If no device_id given, returns all possible command types.

        Args:
            device_id: Device identifier. (Default value = None)

        Returns:
            json: List of command type objects.
        """
        path = self._urls['commands_types']
        params = {}
        if device_id is not None:
            params['deviceId'] = device_id

        req = self._session.get(url=path, params=params)
        if req.status_code == 200:
            return req.json()
        elif req.status_code == 400:
            raise BadRequestException(message=req.text)
        else:
            raise TraccarApiException(info=req.text)
