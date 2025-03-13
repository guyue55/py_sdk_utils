# SDK Utils

A utility library for SDK development that provides common functionality for building Python SDKs.

## Installation

```bash
pip install sdk_utils
```

## Features

- API client utilities
- Authentication helpers
- Rate limiting and retry mechanisms
- Response parsing and error handling
- Logging and debugging tools

## Usage

```python
from sdk_utils.client import APIClient
from sdk_utils.auth import BearerAuth

# Create an authenticated client
client = APIClient(
    base_url="https://api.example.com",
    auth=BearerAuth("your_token_here"),
    timeout=30
)

# Make API requests with automatic retry and error handling
response = client.get("/endpoint", params={"key": "value"})

# Parse the response
data = response.json()
print(data)
```

## Documentation

For full documentation, visit [our documentation site](https://github.com/guyue55/sdk_utils).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.