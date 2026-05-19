# PyTraccar

[![Build Status][travis-image]][travis-url]

## Overview

Python interface to interact with Traccar REST API.

## Python Dependencies
Starting with Debian 12.X(Bookworm), it's best to use a venv (Virtual Environment for Python due to PEP-668 issue)'
Install Python dependencies needed for the scripts using:
`sudo apt install python3-pip python3.11-venv`

Install a Python virtual environment:
`python3 -m venv ~/.venv`

Load the venv: `source ~/.venv/bin/activate`

## Compatibility

- **Traccar**: v6.5 – v6.13.3
- **Python**: 3.8+

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.21 | HTTP client |
| `pytest` | >=4.0.2 | Testing (dev only) |

## Installation

Installation from source:
```sh
git clone git@github.com:kihiukiragu/pytraccar.git
cd pytraccar
pip install -e .
```

## Usage example

_For more info, please refer to the [Traccar API Reference][traccar-api-reference]._

### Authentication

```python
from pytraccar.api import TraccarAPI

# Token-based (recommended)
api = TraccarAPI('https://mytraccaserver.com')
api.login_with_token('YOUR_TOKEN')

# Credentials-based
api = TraccarAPI('https://mytraccaserver.com')
api.login_with_credentials('admin@example.com', 'password')
```

### Sending a command to a device

```python
# Dispatch immediately (200) or queued if device offline (202)
api.send_command(device_id=1, type='positionSingle')

# Custom message via data channel
api.send_command(device_id=1, type='custom', attributes={'data': 'reboot'})

# Save a reusable command
cmd = api.create_command(device_id=1, type='engineStop', description='Kill engine')

# List command types supported by a device
types = api.get_command_types(device_id=1)
```

## Development setup

For testing purposes, set these variables in `tests/test_api_calls.py` to match your Traccar server:

```python
test_url = 'http://127.0.0.1:8082'          # Your Traccar server URL
username, correct_password = 'admin', 'admin' # Credentials for a standard user or admin
user_token  = 'YOUR_USER_TOKEN_HERE'          # Standard user token
admin_token = 'YOUR_ADMIN_TOKEN_HERE'         # Admin user token
```

Run the test suite:
```sh
python -m pytest
```

The unit tests (`test_forbidden_access_exception_*`, `test_set_permissions_guard_*`) run without a live server. All other tests require a running Traccar instance.

## Install Locally
```sh
pip install -e .
```

## API coverage

| Endpoint | Operations | Status |
|----------|-----------|--------|
| `/session` | GET, POST | ✅ tested |
| `/users` | GET, POST | ✅ tested |
| `/devices` | GET, POST, PUT, DELETE | ✅ tested |
| `/geofences` | GET, POST, PUT, DELETE | ✅ tested |
| `/notifications` | GET | ✅ tested |
| `/positions` | GET | ✅ |
| `/groups` | GET | ✅ |
| `/permissions` | POST | ✅ |
| `/reports/events` | GET | ✅ |
| `/reports/trips` | GET | ✅ |
| `/reports/route` | GET | ✅ |
| `/commands` | GET, POST, PUT, DELETE | ✅ tested |
| `/commands/send` | POST | ✅ tested |
| `/commands/types` | GET | ✅ tested |

## Contributing

1. Fork it (<https://github.com/Silverdoses/pytraccar/fork>)
2. Create your feature branch (`git checkout -b feature/yourbranch`)
3. Commit your changes (`git commit -am 'info here'`)
4. Push to the branch (`git push origin feature/yourbranch`)
5. Create a new Pull Request

<!-- Markdown link & img dfn's -->
[travis-image]: https://travis-ci.com/Silverdoses/pytraccar.svg?branch=master
[travis-url]: https://travis-ci.com/Silverdoses/pytraccar
[wiki]: https://github.com/yourname/yourproject/wiki
[traccar-api-reference]: https://www.traccar.org/api-reference/

## Credits

**PyTraccar is built on top of code developed from/by:**
  * Anton Tananaev, https://github.com/tananaev
  * Traccar, https://github.com/traccar/traccar
