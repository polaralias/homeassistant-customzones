# Custom Zone

Custom Zone is a Home Assistant custom component that allows you to define complex polygon-based zones and track whether a specific device is inside them. Unlike the standard Home Assistant zones which are circular, Custom Zone supports arbitrary shapes (polygons) defined by a series of coordinates.

## Features

- **Polygon Zones**: Define zones with any shape (minimum 3 points, up to 15 points).
- **Interactive Configuration**: Easy-to-use Config Flow to add points one by one.
- **Dynamic Feedback**: Real-time updates on the shape type (Triangle, Quadrilateral, etc.) as you add points.
- **Sensor**: Creates a `sensor` entity that indicates if a tracked person is "In zone" or "Not in zone".
- **Ray-casting Algorithm**: Uses the robust ray-casting algorithm to accurately determine point-in-polygon status.
- **Attributes**: The sensor exposes the polygon coordinates and the tracked person entity ID as attributes.

## Installation

### HACS (Home Assistant Community Store)

1. Go to **HACS** > **Integrations**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this repository.
4. Select **Integration** as the category.
5. Click **Add**.
6. Once added, search for **Custom Zone** in HACS and install it.
7. Restart Home Assistant.

### Manual Installation

1. Download the `custom_components/custom_zone` directory from this repository.
2. Copy the `custom_zone` folder into your Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration

Configuration is done entirely through the Home Assistant UI.

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Custom Zone** and select it.
4. Follow the setup wizard:
   - **Zone Name**: Give your zone a friendly name.
   - **Tracked Person**: Select the `person` entity you want to monitor in this zone.
   - **Zone Type**: Currently supports "Polygon".
5. **Add Points**:
   - Enter the **Latitude** and **Longitude** for the first point of your polygon.
   - Click **Submit**.
   - Repeat for subsequent points (minimum 3 required).
   - As you add points, the wizard will tell you how many points you've entered and what shape they form (e.g., Triangle, Quadrilateral).
   - Once you have added all your points (at least 3), check the **Finished adding points** box (which appears after the 2nd point) and click **Submit**.

## Usage

After configuration, a new sensor will be created with the entity ID format:
`sensor.customzone_<person>_<zone>`

### State
- **In zone**: The tracked person is currently inside the defined polygon zone.
- **Not in zone**: The tracked person is outside the defined polygon zone.

### Attributes
- `device`: The entity ID of the tracked person.
- `polygon`: A list of `[latitude, longitude]` pairs defining the zone.

### Example Automation

You can use this sensor in automations just like any other sensor.

```yaml
automation:
  - alias: "Notify when car enters custom zone"
    trigger:
      - platform: state
        entity_id: sensor.customzone_james_home_parking
        from: "Not in zone"
        to: "In zone"
    action:
      - service: notify.mobile_app_my_phone
        data:
          message: "The car has entered the parking zone!"
```
