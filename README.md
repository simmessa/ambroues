# Ambroues

Ambroues is a Python fully automated irrigation system for your KNX enabled home.

## When to use

Ambroues actually makes sense if you have:

- a KNX home automation setup with at least one KNX/IP usable interface on your LAN
- KNX actuators linked to an irrigation system

I've been using the excellent [OpenHAB](https://openhab.org) for my home automation but I'm not really happy
of OpenHAB rules system, so, after setting up my irrigation schedule there I quickly got frustrated with the
general instability and the unnecessary complexity.

Your mileage may vary and maybe your KNX supervisor is far better at this but if you've been looking for 
something simple and quick to learn for your irrigation needs then **Ambroues** is for you!

## Other things you can do with Ambroues

You can automate almost anything which is controlled by your KNX home, so you could also use Ambroues to do some
**presence simulation**, I guess, that's not the usage I had in mind when I wrote this but I guess you can use it  
however you like!

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

Here's an example ambroues.json (you can find it in the repo as ambroues-example.json)

```
{
  "zones": [
    {
      "zone_name": "giardino ovest",
      "zone_knx_address": "1/0/1",
      "zone_enabled": "on",
      "zone_start_time": "06:30",
      "zone_duration_minutes": "10",
      "zone_week_days": ["mon","tue","wed","thu","fri","sat","sun"]
    },
    {
      "zone_name": "giardino sud",
      "zone_knx_address": "1/0/2",
      "zone_enabled": "on",
      "zone_start_time": "06:40",
      "zone_duration_minutes": "10",
      "zone_week_days": ["mon","wed","fri","sun"]
    },
    {
      "zone_name": "giardino est",
      "zone_knx_address": "1/0/3",
      "zone_enabled": "on",
      "zone_start_time": "06:50",
      "zone_duration_minutes": "10",
      "zone_week_days": ["tue","thu","sat"]
    }
  ]
}
```

Every setting should be pretty self explanatory.

## Launching Ambroues

Pretty simple:
```
python ambroues.py
```

## Docker and Ambroues

Ambroues now comes with a pretty decent Docker image!

To build with Docker:
```
docker build . -t ambroues
```
To run with Docker:
```
docker run -d --network host -v /path/to/ambroues.json:/app/ambroues.json ambroues
```
Things to keep in mind:

- You need host networking mode to be able to connect your KNX interface
- A json config file (ambroues.json) is required to define irrigation zones
- This docker container (for x86_64) has been built via multi-stage build so it's kinda slim, about 120 Mb
