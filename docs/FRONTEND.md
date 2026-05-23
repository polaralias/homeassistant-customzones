# Frontend

## Scope

This repository does not have a standalone frontend application.

Its frontend surface is the Home Assistant integration UI:

- config flow forms
- translated copy
- entity naming
- icons and branding
- entity state and attributes as exposed in Home Assistant

## Current verified posture

- the config flow should make valid setup easy and invalid setup obvious
- copy should describe the action the user is taking, not internal implementation details
- entity presentation should support debugging without forcing a user to inspect code
- polygon edits now support keep, append, remove-last, and replace modes within the options flow

## Current frontend constraints

- point-entry ergonomics
- the config flow still cannot offer a graphical or arbitrary point-level polygon editor
- translation completeness
- whether the branding and icon path behave correctly in Home Assistant
