# Changelog

## [1.21.1](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.21.0...v1.21.1) (2026-11-16)


### Bug Fixes

* **api:** Report /State writes the appliance rejects with a Failure entry ([0fc43c9](https://github.com/Gyang91/ha-miele-at-lan/commit/0fc43c909b506d70de01ca8011604d6df55b4a81))

## [1.21.0](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.20.1...v1.21.0) (2026-11-16)


### Features

* **enums:** Name more programme ids and phases and add a shared model_name helper ([60c5a07](https://github.com/Gyang91/ha-miele-at-lan/commit/60c5a07f975c6285d4e7d7f2edb05fd1d7db088f))
* **sensor:** Add programme progress and finish time sensors for cycle appliances ([3916567](https://github.com/Gyang91/ha-miele-at-lan/commit/39165673594f6c8561c78d3ea267644c7018604b))
* **services:** Add an experimental select_program service writing DOP2 2/1577 ([8679853](https://github.com/Gyang91/ha-miele-at-lan/commit/867985356c36b716ebc7f238a22bbd9433f8da76))


### Bug Fixes

* **api:** Cut DOP2 responses at their declared length instead of stripping trailing 0x20 data bytes ([2bec637](https://github.com/Gyang91/ha-miele-at-lan/commit/2bec63787c9e7addc81bbe0f17619533d4f9df11))
* **coordinator:** Poll fast again when the push channel goes quiet mid-programme ([92fac01](https://github.com/Gyang91/ha-miele-at-lan/commit/92fac010df83373b8098d4acd972be6997d75bf2))
* **enums:** Name dishwasher phases 1802-1811 incl. AutoOpen and dryer phase 525 hygiene ([6d238f6](https://github.com/Gyang91/ha-miele-at-lan/commit/6d238f6e7c96a7d5df7f50b5d81c7d1142adf407))
* **enums:** Name dishwasher programmes 206 Hygiene and 208 SolarSave ([10713d0](https://github.com/Gyang91/ha-miele-at-lan/commit/10713d04e6b56c2292fcebbeab88c612a180cf5f))
* **sensor:** Add DOP2 and device-context entities when their data first arrives after setup ([228bcfe](https://github.com/Gyang91/ha-miele-at-lan/commit/228bcfeb7e27dda3bfa1b6269951ac73cd4ad8cf))
* **sensor:** Label Status 144 default and 145 locked instead of unknown ([7044fd1](https://github.com/Gyang91/ha-miele-at-lan/commit/7044fd1792570964135131d32df23c4e6ae90678))
* **sensor:** Translate the push status states ([8f60e14](https://github.com/Gyang91/ha-miele-at-lan/commit/8f60e145a4eab06095454398374571a7896db602))
* **sensor:** Treat Status 10 (idle) as idle so stale programme data is hidden and polling stays slow ([4588241](https://github.com/Gyang91/ha-miele-at-lan/commit/4588241630849b290ebfce652ba1d5134eab1b17))
* **services:** Name and describe the dump REST resource action ([783afe9](https://github.com/Gyang91/ha-miele-at-lan/commit/783afe9807902a20d9b5b9a76687333063203e96))
* **switch:** Show the power switch off for failure and not-connected appliances, unknown without a status ([ddba8d0](https://github.com/Gyang91/ha-miele-at-lan/commit/ddba8d0815b6784d19fc9de7e5f49a863458e730))
* **tools:** Save provisioning keys to a gitignored keys.yaml by default ([d05b106](https://github.com/Gyang91/ha-miele-at-lan/commit/d05b1061a001d6c593205bcf274c86db98afc447))

## [1.20.1](https://github.com/Gyang91/ha-miele-at-lan/compare/v1.20.0...v1.20.1) (2026-11-12)


### Bug Fixes

* scope Gitleaks exception to historical false positives ([f98417c](https://github.com/Gyang91/ha-miele-at-lan/commit/f98417ca91db48b4e2a5de8486e315dc7b0788fb))

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
