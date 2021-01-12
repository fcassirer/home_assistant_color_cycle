# Color Cycle
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

_Provides a number of color cycle effects for any set of color bulbs

## Lovelace Example

![Example of the entities in Lovelace](https://github.com/fcassirer/home_assistant_color_cycle/blob/master/colorcycle_entities.png)

## Installation

TBD: Install via [HACS](https://github.com/custom-components/hacs), so that you can easily track and download updates.

Alternatively, you can download the `home_assistant_color_cycle` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `colorcycle` module.

## How it works

After creating a few helpers, this app allows you to select a list of lights, either by entity name or using a group.  From there, a number of predefined effects such as `random`, `strobe`, `wave`, etc can be chosen from the corresponding input_select helper.




## AppDaemon Libraries

Please add the following packages to your appdaemon 4 configuration on the supervisor page of the add-on.

``` yaml
system_packages: []
python_packages: []
init_commands: []
```

## App configuration

In the apps.yaml file in the appdaemon/apps directory -

```yaml
dockColorCycle:
  module: colorcycle
  class: ColorCycle
  log: diag_log
  lights: [ "group.dock_lights"]
  helper_effect: input_select.dock_effect
  helper_color: input_select.dock_effect_colors
  helper_color_options:
    rgby: [ "red", "green", "blue", "yellow" ]
    rainbow: [ "red", "blue", "green", "yellow", "purple",  "crimson", "darkcyan", "orange"]
    blues: [ "#blue", "#cyan", "#turquoise" ]
    reds: [ "#red", "#crimson", "#pink" ]
    xmas: [ "red", "green"]
    greens: [ "#green" ]
    yellows: [ "#yellow" ]

  # speed in seconds
  helper_speed: input_number.dock_effects_speed
  fade: True
  brightness: 100
  color_temp: "2750"
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | required | string | | `colorcycle`
`class` | required | string | | `ColorCycle`
`lights` | required | list | | The list of color capable light entities.  This can be any combination of groups and/or individual entities
`helper_effect` | required | input_select | | Name of an input select for selecting effects (see helpers/select/colorcycle_select.yaml
`helper_color` |  required | input_select | | Name of an input select for selecting color sets (see helpers/select/colorcycle_select.yaml
`helper_color_options` | required | yaml dict | | Selectable color combinations, subset of w3color table.  helper_color input_select is updated to match this config
`helper_speed` | required | number_select | | Name of an input_number helper to control duration in seconds for each effect

## Issues/Feature Requests

Please log any issues or feature requests in this GitHub repository for me to review.
