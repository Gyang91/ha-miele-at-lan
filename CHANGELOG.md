# Changelog

## [1.20.0](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.19.0...v1.20.0) (2026-11-09)


### Features

* **switch:** Add the power switch for tumble dryers ([7d90915](https://github.com/Gyang91/ha-miele-at-lan/commit/7d90915f2957ec54e2ff086ceb18c1439d4e8a1f))

## [1.19.0](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.18.1...v1.19.0) (2026-11-09)


### Features

* **sensor:** Add energy and water consumption of the running program ([276cdca](https://github.com/Gyang91/ha-miele-at-lan/commit/276cdcab66c1ed8a4684c8b590f5c684ea4ed840))
* **sensor:** Add lifetime energy and water consumption from DOP2 2/1585 ([68b8729](https://github.com/Gyang91/ha-miele-at-lan/commit/68b8729a256e1a3b398ec78eb880e26d2864691b))

## [1.18.1](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.18.0...v1.18.1) (2026-11-09)


### Bug Fixes

* **coordinator:** Keep polling while an appliance pushes ([99bf9ae](https://github.com/Gyang91/ha-miele-at-lan/commit/99bf9ae0bd26989ab993558a850d6dd3e5d0d13f))
* **sensor:** Add 2/1585 entities once the appliance first answers ([c872088](https://github.com/Gyang91/ha-miele-at-lan/commit/c87208899f7c26e00f83ab7769d2c5100fbf3930))

## [1.18.0](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.17.1-fork.1...v1.18.0) (2026-11-09)


### Features

* **sensor:** Add program start and end times and a Smart Grid flag ([8a32562](https://github.com/Gyang91/ha-miele-at-lan/commit/8a325622646358b871c1e1b84d6aba8a67c8cc3a))


### Bug Fixes

* **api:** Report dropped connections readably and send one request at a time ([b9d0ecc](https://github.com/Gyang91/ha-miele-at-lan/commit/b9d0ecc6e07d20f270fab81eb2d8a7baabcfc0eb))
* **sensor:** Create TwinDos entities for washers only ([5c53986](https://github.com/Gyang91/ha-miele-at-lan/commit/5c5398608b26dc544113b6303eb0a51f9a612061))


### Code Refactoring

* Keep per-entry state in a typed entry.runtime_data ([bd9436e](https://github.com/Gyang91/ha-miele-at-lan/commit/bd9436e7978bd5ef7904a438ee11cd956728950f))

## [1.17.1-fork.1](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.17.1...v1.17.1-fork.1) (2026-11-09)


### Bug Fixes

* **coordinator:** Never wake the appliance for the background device-context read ([8fc8644](https://github.com/Gyang91/ha-miele-at-lan/commit/8fc86448e78d08a5cf8488d8bb70472a3b7749f4))


### Miscellaneous

* Release 1.17.1-fork.1 ([66c0f72](https://github.com/Gyang91/ha-miele-at-lan/commit/66c0f721be74a9a0cb43d805451c912783d7340c))
