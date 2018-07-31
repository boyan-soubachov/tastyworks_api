# Tastyworks (Unofficial) API

## Disclaimer

This is an unofficial, reverse-engineered API for Tastyworks. There is no implied warranty for any actions and results which arise from using it.

## Purpose

A simple, async-based, reverse-engineered API for tastyworks. This will allow you to create trading algorithms for whatever strategies you may have.

Please note that this is in the very early stages of development so any and all contributions are welcome. Please submit an issue and/or a pull request.

## Installation
```
pip install tastyworks
```
✨ 🍰

Since it's an async-based API, please make sure you're familiar with how asynchronous python works (Note: Python 3.6 or higher).

An example use is provided in `example.py` in the `tastyworks` folder. See for yourself by adding your tastyworks username/password and running:

```
tasty 
```

## Guidelines and caveats

There are a few useful things to know which will help you get the most out of this API and use it in the way it was intended.

1. All objects are designed to be independent of each other in their _steady-state_. That is, unless executing an action, all objects are not bound to each other and have no knowledge of each other's awareness.
1. One can have multiple sessions and, due to the inter-object independence, can execute identical actions on identical objects in different sessions.
1. Given the above points, this API *does not* implement state management and synchronization (i.e. are my local object representations identical to the remote [Tastyworks] ones?). This is not an indefinitely closed matter and may be re-evaluated if the need arises.

## Contributing

The more hands and brains that can help with this project, the better. It was implemented with the effort of getting something working rather than something beautiful as it is a reverse-engineering effort in progress.
I would appreciate any input (be it in the form of issue reporting or code) on how to make this code-base better.

You can find the official GitHub repo at: https://github.com/boyan-soubachov/tastyworks_api

## TODO

I would really appreciate any help/contributions with the TODO's scattered all around the codebase. If they're not descriptive enough, I'd be happy to provide more details.
