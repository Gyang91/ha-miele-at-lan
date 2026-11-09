<p align="center">
  <img alt="Miele@LAN" src="custom_components/miele_lan/brand/icon@2x.png" width="128"/>
</p>

<h1 align="center">Miele@LAN</h1>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Gyang91&repository=ha-miele-at-lan&category=integration"><img alt="Open in HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg"/></a>
</p>
<p align="center">
  <a href="https://github.com/Gyang91/ha-miele-at-lan/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/Gyang91/ha-miele-at-lan?label=release"/></a>
  <a href="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/ci.yml/badge.svg"/></a>
  <a href="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/validate.yml"><img alt="Validate" src="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/validate.yml/badge.svg"/></a>
  <a href="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/security-audit.yml"><img alt="Security audit" src="https://github.com/Gyang91/ha-miele-at-lan/actions/workflows/security-audit.yml/badge.svg"/></a>
  <a href="https://www.home-assistant.io"><img alt="HA 2024.12+" src="https://img.shields.io/badge/HA-2024.12%2B-blue.svg"/></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/Gyang91/ha-miele-at-lan.svg"/></a>
</p>

Local Home Assistant integration for Miele@home appliances. Talks directly to the appliance over the LAN: no cloud account at runtime, no sidecar server, no Miele 3rd-party API.

Fork of [tiehfood/ha-miele-at-lan](https://github.com/tiehfood/ha-miele-at-lan). Same domain (`miele_lan`), so it replaces the original in place. Version numbers are this fork's own. Differences: [Fork changes](#fork-changes). History: [CHANGELOG.md](CHANGELOG.md).

## Features

- Miele's local REST + DOP2 binary protocol: `MieleH256` HMAC-SHA256 + AES-CBC, signed with the household `GroupKey`.
- Real-time state via Miele's **SuperVision push**. Polling runs alongside: every 60 s, every 10 s while a programme runs on an appliance without push.
- Never wakes an appliance in the background. Waking happens only on a user action (wake button, power switch).
- mDNS auto-discovery (`_mieleathome._tcp`): one config flow adds every appliance in the household.
- Provisioning tool for factory-fresh appliances: `tools/miele_lan_provision.py`.
- Optional Miele cloud OAuth pairing: fetches the household `GroupKey` once; the Miele app keeps working.
- Cooling appliances are read-only (see [Limitations](#limitations)).

## Supported appliances

| Family | Models | Sensors | Controls |
|---|---|---|---|
| **Oven** (incl. steam, combi, microwave) | H7560BP, H7164BP, DGC7860HCXL, DGM7440, … | status, program, phase, remaining/elapsed/start-in, program start/end time, cavity & core temps, target & core-target, door, signals, light | stop, wake, power, light |
| **Hob** | KM7576, KM7895 FL induction, induction + extractor | per-zone power (1..12 incl. ½ steps, boost/boost+, keep-warm), residual heat, timer, status | — |
| **Dishwasher** | G7000 series, semi-pro/professional | status, program, phase, remaining/elapsed/start-in, program start/end time, door, signals, AutoDos, salt, rinse aid, lifetime energy & water ¹ | start / stop / pause / resume, wake, power |
| **Washing machine** | WWG/WWV/WWI/WTV series | status, program, phase, spin speed, target temp, remaining/elapsed/start-in, program start/end time, door, signals, Smart Grid, TwinDos levels & Wash2Dry ¹ | start / stop, wake |
| **Tumble dryer** | TWC/TWV/TMV series | status, program, phase, drying step, remaining/elapsed/start-in, program start/end time, door, signals, Smart Grid, Wash2Dry, energy per program & lifetime ¹ | start / stop, wake, power ² |
| **Fridge / freezer / fridge-freezer** | KF 7772 B, K 7000, KFN, KFNS, … | per-zone current & target temp, per-zone door, SuperCool, SuperFreeze, failure | — (see [Limitations](#limitations)) |
| **Wine cabinet** | KWT 6000, KWNS, KWTUS, wine + freezer | per-zone temp, per-zone door, light state | — (see [Limitations](#limitations)) |
| **Hood / range vent** | DA series, EK039W | fan step, light state, grease & charcoal filter saturation ³ | fan (off / 1-3 / boost) ³, fan run-on time ³, light, power ⁴ |
| **Coffee system** | CVA series | status | wake, power, light |
| **Dish warmer** | ESW series | status, door | wake, power |

Diagnostic entities (raw enums, WLAN info, push state, firmware version) are created but disabled by default. Enable them per device under **Configure entities**.

1. From DOP2 leaf `2/1585`. Only where the WiFi module exposes DOP2 (not on EK057 washers with firmware 08.x). Read only while the appliance is on; the entities appear once the leaf first answers. Energy in Wh and water in L are the appliance's own counters (`total_increasing`, Energy dashboard ready); program counters restart with each program.
2. DOP2 leaf `2/1586`. Tested on an EK037 module: off within a second; on via wake-and-retry.
3. Legacy Dop1 protocol, used for hoods reporting `ProtocolVersion 2`, as the official Miele app does. Hoods reporting 3/4 keep the read-only fan step and the light, and get a power switch instead.
4. Only for hoods reporting `ProtocolVersion 3/4`. On Dop1 hoods the fan entity covers on/off, and GLOBAL_USER_REQ (the switch's fallback) answers HTTP 404.

### Integrated extractor speed (KMDA7876)

Read-only **Extractor speed** sensor (Off, 1–3, Boost) and read-only **Extractor** fan entity (0 / 25 / 50 / 75 / 100 %, 100 % = Boost). Discrete steps, not measured airflow. No fan control.

## Installation

### HACS

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Gyang91&repository=ha-miele-at-lan&category=integration)

Or: HACS → ⋮ → Custom repositories → `https://github.com/Gyang91/ha-miele-at-lan`, type **Integration** → download → restart HA.

Switching from the original repository: remove `tiehfood/ha-miele-at-lan` in HACS, add this one, download, restart. Config entries, devices and entity IDs are kept.

### Manual

Copy `custom_components/miele_lan/` to `<config>/custom_components/miele_lan/` and restart.

### Adding your household

**Settings → Devices & services → Add Integration → Miele@LAN.** Three setup paths:

- **Cloud pairing (recommended).** Log in once with your Miele account; HA fetches the household `GroupKey`, mDNS-discovers every appliance and provisions a SuperVision push listener. The Miele app keeps working. Pick the country your Miele *account* is registered with (the sales company, not necessarily where you live); HA finds the regional backend itself.
- **Paste pre-obtained tokens.** An `access_token` + `refresh_token` from a Miele OAuth flow against `prod.map.miele-iot.com`.
- **Paste household credentials.** `GroupID` + `GroupKey` (e.g. from `MieleRESTServer`). No cloud round-trip; works for every country.

Factory-fresh appliances: run `python tools/miele_lan_provision.py` first. It writes a new `GroupID`/`GroupKey` and binds the appliance to your LAN.

> **Warning:** the appliance does not validate commissioning payloads. An empty `GroupKey` or a `GroupID` of `0` is accepted with `200 OK`; every later write of the real keys is then refused with `403 Forbidden`. Recovery only on the appliance: settings → **Miele@home** → reset, then reconnect in the Miele app. Use `tools/miele_lan_provision.py`, which validates key lengths.

### Supported countries (cloud pairing)

Every sales company Miele's MAP gateway serves (49 at the time of writing):

```
ae at au be bg br ca ch cl cn cy cz de dk ee es fi fr gb gr hk hr hu ie in it jp kr
lt lu lv mx my nl no nz pl pt ro rs se sg si sk th tr ua us za
```

Check against the live gateway:

```sh
python tools/dump_map_countries.py --check    # exits non-zero if Miele changed anything
```

Country missing: use **Paste household credentials** (region-independent).

### Capturing the OAuth redirect (cloud pairing)

The login ends with a `miele://oauth2-code/?code=…&state=…` redirect that browsers refuse to open. Grab it from the network log:

1. Open the authorization URL from the config flow in **Chrome / Edge on a desktop**.
2. Open **DevTools → Network** (F12) **before** logging in; enable *Preserve log*.
3. Log in with your Miele account.
4. Find the **last request whose URL starts with `miele://`** (blocked, usually red).
5. Right-click → *Copy → Copy link address*.
6. Paste the full URL into the config flow.

Firefox: DevTools → Network → the blocked `miele://` redirect.

## How to

Entity IDs follow the device name; replace `my_washer` / `my_dryer` with yours.

### Get notified when a program has finished

```yaml
triggers:
  - trigger: state
    entity_id: sensor.my_washer_status
    to: program_ended
actions:
  - action: notify.mobile_app_my_phone
    data:
      message: The washing machine has finished.
```

### Show when the laundry will be done

Add `sensor.my_washer_program_end` to a dashboard (e.g. a Tile card). It shows the expected end time and stays after the program ends until the appliance is switched off. For a delayed start it includes the delay.

### Add the dryer to the Energy dashboard

**Settings → Dashboards → Energy → Individual devices → Add device** → `sensor.my_dryer_lifetime_energy_consumption`. Only for appliances that report the counter (see [Supported appliances](#supported-appliances), footnote 1).

### Switch the dryer off after it has finished

```yaml
triggers:
  - trigger: state
    entity_id: sensor.my_dryer_status
    to: program_ended
    for:
      minutes: 30
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.my_dryer_power
```

### Start a program from Home Assistant

Program selection is not possible over the LAN, so prepare it on the appliance:

1. Choose the program on the panel.
2. Press the appliance's **remote start** (MobileStart) button. `binary_sensor.my_washer_mobile_start` turns on.
3. Press `button.my_washer_start` (or use it in an automation).

Start needs remote control enabled on the appliance, and is refused while mobile start is off or a delayed start is set; the error names the reason.

## Limitations

- **Fridges, freezers and wine cabinets are read-only.** K7000/EasyControl firmware (XKM `EK057*`) has no LAN write path; every PUT/POST returns HTTP 403 (verified on a KF 7772 B). The Miele app writes via a device-initiated cloud WebSocket. [Miele's documentation](https://www.miele.de/support/customer-assistance/app-1199/alle_kategorien/mobilecontrol_und_mobilestart-132299522827): MobileStart is permanently on and not togglable on cooling appliances. State changes still arrive in real time via push.
- **Washers with an EK057 module (firmware 08.x)** expose no DOP2 at all (no `DOP2` resource, every leaf 404). Without DOP2: no TwinDos levels, no energy/water, no Wash2Dry, no power switch. Over `/State` they accept `{"DeviceAction": 2}` but stay off, and refuse `{"DeviceAction": 3}` with HTTP 400. Tested on a WWI860.
- **Energy and water** need DOP2 `2/1585` or a model-specific `/State.ExtendedState`.
- **No program selection.** Start only runs the program chosen on the panel.
- **No firmware update trigger.** `/Update/` is read-only.
- **`Mobile Controllable`** must be enabled on the panel for writes to cycle appliances (oven, dishwasher, washer, dryer).
- **One household per HA install.**
- **mDNS required.** HA and the appliances must share a broadcast domain (same VLAN, no Docker bridge, no IoT-VLAN isolation).

## Troubleshooting

**Appliance not discovered.** Check that HA receives Miele mDNS (HA terminal app or SSH):

```sh
# Home Assistant OS / Debian / most Linux
avahi-browse -rt _mieleathome._tcp
# macOS
dns-sd -B _mieleathome._tcp local.
```

Nothing listed: the network drops multicast. Usual causes: IGMP snooping without an IGMP querier, a VLAN ACL, an mDNS-blocking firewall rule, HA in a Docker bridge (use `network_mode: host`).

**"household … has no appliances".** Check the log for a second line naming a *different* household: the appliances were commissioned into an earlier household than the one your account owns. Re-pair them in the Miele app, or use **Paste household credentials** with the GroupKey of the household they advertise. If no Miele appliance answered mDNS at all, it is a network problem (see above).

**One appliance missing.** The integration raises a **repair issue** naming it. Usually the appliance was never fully commissioned: its mDNS TXT record shows `group=` with nothing after it (compare with a working appliance using the commands above). Fix: appliance settings → **Miele@home** → reset, then reconnect in the Miele app.

**Push not working (updates only every 60 s).** Enable `Mobile Controllable` on the appliance; make sure HA's listener port (default 18082) is reachable from the appliance subnet. The diagnostic **Push status** sensor shows `push:active` when push works.

**`HTTP error 403` on writes.** `Mobile Controllable` is off on the panel. Cooling appliances always answer 403 (see [Limitations](#limitations)).

**Debug logs:**

```yaml
logger:
  logs:
    custom_components.miele_lan: debug
    asyncmiele: debug
```

**Raw data for bug reports.** Services `miele_lan.dump_dop2_leaf` and `miele_lan.dump_rest_resource` read one DOP2 leaf or REST resource and return it (read-only).

## Development

```sh
git clone https://github.com/Gyang91/ha-miele-at-lan
cd ha-miele-at-lan
python3.14 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest tests/ -q
```

Parser and protocol tests need no running Home Assistant.

## Fork changes

Differences from upstream [tiehfood/ha-miele-at-lan](https://github.com/tiehfood/ha-miele-at-lan) v1.17.1:

| Area | Change |
|---|---|
| Standby | Background polling never wakes an appliance. DOP2 `2/1585` is skipped while the appliance is off; a 500 while idle means "asleep" and never latches the leaf unsupported. Before, `PUT /State {"DeviceAction": 2}` every 10 minutes kept washers, dryers and dishwashers out of standby (drum light switching on at night). |
| Polling | Push no longer restarts the poll timer, so poll-only data (DOP2 `2/1585`, WLAN, hours of operation) stays current during a program. |
| Entities | DOP2 `2/1585` entities appear once the leaf first answers, not only at setup. TwinDos entities only on washers. |
| New sensors | Program start / end time (all cycle appliances), Smart Grid, energy and water per program and lifetime. |
| New controls | Power switch for tumble dryers. |
| Reliability | All network errors reported readably; one request at a time per appliance. |
| Code | Typed `entry.runtime_data`, shared error mapping, unused imports removed. |
| Maintenance | release-please releases, CI (Python 3.14 / HA 2026.11), HACS + hassfest validation, daily security audit (pip-audit, OSV-Scanner, Gitleaks, dependency review), Dependabot. |

Releases follow conventional commits: `feat:`, `fix:` and `perf:` release; `chore:`, `ci:`, `docs:` and `test:` do not.

## Disclaimer

This project is independent and not affiliated with, endorsed by, or supported by Miele & Cie. KG. **Miele®** and **Miele@home®** are registered trademarks of Miele & Cie. KG; the appliance model names (KM, H, DGC, G, WWG, TWC, KF, KFN, KWT, KWNS, ESW, CVA, DA) are likewise Miele trademarks used here purely for identification. Use of this software may void your appliance warranty — use at your own risk.

The brand icons at `custom_components/miele_lan/brand/` (also shown at the top of this page) are the property of Miele & Cie. KG and are bundled so Home Assistant can show the manufacturer logo on the device card. If a Miele representative would like them removed or replaced, please open an issue.

## Credits

Built on years of prior reverse-engineering. Thanks to:

- **[akappner](https://github.com/akappner)** — [`MieleRESTServer`](https://github.com/akappner/MieleRESTServer), [`asyncmiele`](https://pypi.org/project/asyncmiele/), and [`dop2rs`](https://github.com/akappner/dop2rs). Original public RE of `MieleH256`, DOP2, and the provisioning flow.
- **[schneidair](https://community.home-assistant.io/u/schneidair)** — independent discovery of the `MielePairing:Pairing` auth on EK057S.
- **[ajander](https://community.home-assistant.io/u/ajander)** — SpeedOven commissioning pcap.
- **[astrandb](https://github.com/astrandb)** + the HA core Miele maintainers — upstream cloud integration and [`pymiele`](https://pypi.org/project/pymiele/), used here for cross-reference.
- **[tiehfood](https://github.com/tiehfood)** — the original Miele@LAN integration this fork is based on.
- **HA Community thread [#840093](https://community.home-assistant.io/t/mielerestserver-miele-home-without-cloud-possible/840093)** contributors — for surfacing SuperVision, model quirks, and the OTA hosts.
