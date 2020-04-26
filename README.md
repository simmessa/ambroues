# Ambroues

I have a KNX enabled automated house and I needed something to water my lawn with so... here you go!

## Install

You need Python3 for Ambroues, and he gives his best in a virtualenv... make sure you install the requirements.txt!

```
virtualenv --python=python3
pip3 install -r requirements.txt
```

## Configuration

Since Ambroues uses knx for sending watering signals, you need two things:

1) A working xknx.yaml (please look at xknx-example.yaml for inspiration)
2) A zones configuration file called "ambroues.json"

Here's an example ambroues.json:

```
{
  "zones": [
    {
      "zone_name": "giardino ovest",
      "zone_knx_address": "1/0/1",
      "zone_enabled": "on",
      "zone_start_time": "06:30:00",
      "zone_duration_minutes": "10",
      "zone_week_days": ["mon","tue","wed","thu","fri","sat","sun"]
    },
    {
      "zone_name": "giardino sud",
      "zone_knx_address": "1/0/2",
      "zone_enabled": "on",
      "zone_start_time": "06:40:00",
      "zone_duration_minutes": "10",
      "zone_week_days": ["mon","wed","fri","sun"]
    },
    {
      "zone_name": "giardino est",
      "zone_knx_address": "1/0/3",
      "zone_enabled": "on",
      "zone_start_time": "06:50:00",
      "zone_duration_minutes": "10",
      "zone_week_days": ["tue","thu","sat"]
    }
  ]
}
```

Every setting should be pretty self explanatory.

##  Docker

A docker container is in the works... stay tuned!