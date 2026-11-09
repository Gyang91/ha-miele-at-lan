# Changelog (fork)

Upstream releases are listed on
[tiehfood/ha-miele-at-lan](https://github.com/tiehfood/ha-miele-at-lan/releases).
This file only covers changes made in this fork.

## 1.17.1-fork.1

Based on upstream v1.17.1 (commit `d1fd482`).

### Fixed

- **Background polling no longer wakes appliances.** The device-context read
  (DOP2 `2/1585`: TwinDos, Wash2Dry, salt/rinse aid, AutoDos) ran every 10
  minutes for washers, dryers and dishwashers. On HTTP 500 (XKM asleep) it sent
  `PUT /State {"DeviceAction": 2}` and read again. When the wake worked, the miss
  counter reset, so the appliance was woken every 10 minutes, day and night.
  On a dryer this shows as the drum light switching on while the machine is off.

  New behaviour of `_maybe_refresh_device_context`:
  - It never calls `wake()`.
  - `/State.Status` off (1) or not_connected (255): the read is skipped. The
    throttle is not advanced, so the read happens on the first poll after the
    appliance is switched on.
  - No programme running (Status other than in_use): a 500 or a fetch failure
    means "asleep". The last value is kept, and it does not count as a miss, so
    a sleeping appliance is never latched unsupported (G7655 case).
  - Programme running (Status in_use, XKM awake): a 500 or a fetch failure
    counts as a miss. 3 consecutive misses latch the leaf unsupported, as before
    (issue #16, G7310, error codes 20660/28701). 403/404 still latch at once.

  Waking after a user action is unchanged: the wake button and the power switch
  (`set_power`) still wake the appliance.

### Notes

- Trade-off: consumable levels (salt, rinse aid, TwinDos) now refresh only while
  the appliance is on, not while it sleeps.
- The 60 s `/State` poll is unchanged. Whether that request alone wakes an
  appliance is not known.
