# Moisture Meters

## Devices

| Device  | Tested  | Connection |
| ------- | ------- | ---------- |
| **IVG 1/1** | 02/2023 | RS-485 |

## Functions

### moisture_meter_name() { #moisture_meter_name data-toc-label="moisture_meter_name" }

```python
moisture_meter_name()    # -> str; device name
```

The function returns device name.

---

### moisture_meter_meter() { #moisture_meter_meter data-toc-label="moisture_meter_meter" }

```python
moisture_meter_meter()    # -> list(4); measured data
```

This function returns a list with the measured data and is only called without arguments. The format of the measured data is the following: `['dew point in deg. C', 'water content in ppm', 'water content in mg/m^3', 'temperature in deg. C']`.
