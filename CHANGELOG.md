# Changelog
All important and notable changes will be documented here.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2018-08-13

### Added
- Added a new, rewritten `get_option_chain` method to the `Underlying` model, which is inherited by
    models like `Stock` and all other future representations of securities.
- New `Security` model representing all securities (options and underlyings).
- New `Underlying` model representing all underlyings (stocks, indices, ETFs).
- New `OptionChain` model which represents an option chain (a collection of options). This should make
    management of a list of related options (i.e. for a ticker) easier.

### Removed
- The `get_option_chains` function from the TastyAPISession.
- The `Model` model


## [2.1.0] - 2018-07-31

### Added
- Option model to store information about individual option legs
- Ability to execute options successfully (the last missing bit was option legs)
- Added first set of unit tests.

## [2.0.0] - 2018-07-30

### Added
- OrderDetails object to encapsulate order-specific details

### Changed
- Internal changes and refactors to the orders model
- Re-architecture of the API _modus operandi_. Details in the README.md file.
- Moved the remote-fetching of objects (e.g. Order, TradingAccount) to their relevant object models.

### Removed
- Trimmed down remote-fetching of objects from the TastyAPISession object, it is now a much more
    light-weight object.

## [1.0.0] - 2018-07-24
*NB: This is backwards-incompatible*

### Added

#### Orders
- Class describing orders (Order)
- Ability to get existing account orders

#### Trading accounts
- Class for trading accounts (TradingAccount)

### Changed
- Changed the session creation code, please see the new example file
