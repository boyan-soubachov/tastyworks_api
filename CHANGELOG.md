# Changelog
All important and notable changes will be documented here.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2019-02-26

### Changed
- Changed the underlying streamer connection to use `aiocometd` rather than our own, custom-rolled
    transport.

## [3.1.2] - 2019-02-19

### Added
- The `time-in-force` and `gtc-date` properties to the OrderDetails object

### Changed
- Example script now uses env vars for TastyWorks username/password instead of hard-coding values.

## [3.1.1] - 2019-01-16

### Added
- The `rejected` order status type

### Changed
- Fixed bug with in the `Quote` mapped item to support the new time fields
- Removed the `time` key from the `Quote` mapped item
- Fix bug for missing `price` field in the `Order` model

## [3.0.1] - 2018-09-11

### Changed
- Changed number formats to use decimal types instead of floats for predictable representations

## [3.0.0] - 2018-08-20

### Changed
- Fixed a bug which prevented orders from executing altogether... big one.

### Removed
- The `underlying_symbol` field from the `Order` model, this is not necessary and tastyworks does not have
    the symbol tied to an order; they are tied to individual legs of the order.

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
