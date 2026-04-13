# Thingsboard API Docs

## Background
The web app communicates with the edge devices (Raspberry Pi) using the Thingsboard platform. We do this, on the web app end, using the Thingsboard REST API, which will communicate with the edge device using MQTT.

## MQTT Telemetry
The Pi communicates with Thingsboard primarily by sending telemetry signals to Thingsboard using MQTT.
The Pi sends JSON to this MQTT endpoint:

    v1/devices/me/telemetry

The server can get this data from the Thingsboard REST API using this endpoint:
    /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries

## MQTT Attributes
This is used to send attributes to Thingsboard, which can be used for device management and configuration. The Pi sends JSON to this MQTT endpoint:
    v1/devices/me/attributes

and the server can get this data from the Thingsboard REST API using this endpoint:
    /api/plugins/telemetry/DEVICE/{deviceId}/values/attributes

## MQTT RPC
This is used for remote procedure calls, allowing the server to send commands to the Pi. The server can send RPC commands to the Pi using the Thingsboard REST API endpoint:
    /api/plugins/rpc/DEVICE/{deviceId}

The Pi listens for RPC commands on this MQTT topic:
    v1/devices/me/rpc/request/+

## Our Implementation
### Device Setup
When the user signs up using their device's ID, we need to send the Local Authority information to the device. For this, we will use MQTT Attributes with a shared scope. The web app sets the Local Authority information as a shared attribute for the device, and the Pi listens for changes to this attribute to get the Local Authority information.

#### Example attribute setting
POST http://thingsboard.cs.cf.ac.uk:80/api/plugins/telemetry/DEVICE/{id}/attributes/SHARED_SCOPE

```json
{"localAuthorityId": "{id}"}
```

*Note, this assumes that local authority IDs will be shared across devices, otherwise it won't know what the name of the Local Authority is.*  

### Telemetry (Camera Data)
To collect the statistics for the camera data, the Pi will send telemetry data to Thingsboard every time a detection occurs. This telemetry data will include the timestamp, the type of waste detected (e.g. plastic, cardboard), and any other relevant information (e.g., confidence level). The web app can then retrieve this telemetry data from Thingsboard to display it to the user.

### Next Collection Reminders
The reminders for the next waste collection will also be implemented with shared attributes. 
