import json
import appdaemon.plugins.hass.hassapi as hass
import re
import inspect
from datetime import datetime
import random

#
# Color Cycle
#
# Args:
#


class ColorCycle(hass.Hass):

  req_args = ["lights","helper_color","fade","helper_speed","helper_effect"]
  colors = {}

  def load_color_file(self,name):
    colors = []
    try:
      with open (name) as f:
        for line in f.readlines():
          names = line.split()
          colors = colors + names
    except FileNotFoundError:
      pass

    return colors

  def load_w3colors(self):
    self.w3colors = {}
    with open ('/config/w3colors') as f:
      for line in f.readlines():
        name,hexval,rgb = line.split()
        self.w3colors[name] = [hexval,rgb]

  def load_colors(self):
    self.load_w3colors()
    options = { 'w3colors' : list(self.w3colors.keys()) }
    colorset = self.args["helper_color_options"]
    self.debug("colorset is: ")
    self.debug(list(colorset.keys()))

    for k in colorset.keys():
      options[k] = []
      for c in colorset[k]:

        if c[0] == '@':
          options[k] = options[k] + self.load_color_file("/config/" + c[1:])
          continue

        if c[0] == '#':
          rx = c[1:]
          for w in options['w3colors']:
            mobj = re.search(rx,w)
            if mobj:
              options[k].append(w)
          continue

        options[k].append(c)
      self.debug("options["+k+"]="+",".join(options[k]))

    # Configure our color selector based on the apps.yaml settings
    # preserve the old section across restarts of app

    prev_sel = self.get_state(self.args['helper_color'])
    self.debug("Current setting is "+prev_sel)
    self.debug("Options are: "+",".join(list(options.keys())))

    #               attributes={'options': list(options.keys()) },
    #               replace = True)

    self.call_service("input_select/set_options",
                      entity_id=self.args['helper_color'],
                      options= list(options.keys()))

    new_state = self.set_state(self.args['helper_color'],
                               state=prev_sel,
                               attributes={'options' : list(options.keys()),
                                           'friendly_name' : "Dock effects cycle time",
                                           'icon': 'mdi:palette'})
    self.debug("new: {}".format(new_state))
    new_state = self.get_state(self.args['helper_color'],attribute="all")
    self.debug("new: {}".format(new_state))

    self.color_options = options

  def initialize(self):
    self.log("Hello from ColorCycle app, myname={}".format(self.name))
    self.log("You are now ready to run Apps!")
    missing = []
    self.log("args: {}".format(",".join(self.args)))
    for argcheck in self.req_args:
      if argcheck not in self.args:
        missing.append(argcheck)
    if len(missing) != 0:
      self.log("Missing required parameters: {}".format(",".join(missing)))
      return

    if self.args["log"] in  ["debug_log","test_log","diag_log"]:
      self.debugmode = True
      self.log("Enabling debug output")
    else:
      self.debugmode = False

    self.lights = []

    self.speed = float(self.get_state(self.args["helper_speed"]))
    self.debug("Speed is {}".format(self.speed))
    self.fade = self.args["fade"]
    self.brightness = self.args.get("brightness",100)
    self.color_temp = self.color_temperature_to_value(self.args.get("color_temp","cool"))
    self.timer = None
    self.effect = None

    # Initialize the effect state args variable to initial state
    self.effect_state = None

    self.load_colors()
    color_choice = self.get_state(self.args['helper_color'])
    self.colors = self.color_options[color_choice]
    self.debug("Set color choice to "+color_choice)

    self.debug(self.colors)

    self.listen_state(self.setcolor_choice,self.args['helper_color'])
    self.listen_state(self.setspeed_choice, self.args['helper_speed'])

    helper = self.args['helper_effect']
    self.listen_state(self.cycle,helper)

    for eid in self.args["lights"]:
      if "group" in eid:
        self.lights = self.lights + self.get_group(eid)
      else:
        self.lights.append(eid)

    for e in self.lights:
      self.debug("light found: "+e)

    # Handle initial set is already on when we get here
    self.effect_name = self.get_state(helper).lower()
    if self.effect_name != "off":
      self.cycle(helper,None,"",self.effect_name,{})

  def setcolor_choice(self, entity, attribute, old, new, kwargs):
    if new != "":
      self.colors = self.color_options[new]
      self.debug("Setting color selector to "+new)
      self.cycle(self.args['helper_effect'],None,"",self.effect_name,{})

  def setspeed_choice(self, entity, attribute, old, new, kwargs):
    if new != "":
      self.speed = float(new)
      self.debug("Speed is {}".format(self.speed))
      self.cycle(self.args['helper_effect'],None,"",self.effect_name,{})

  # Manage the various event states of the machine
  def postevent(self,reason,kwargs={}):
    self.log("Posting event '{}' : '{}'".format(reason,self.event_list[reason]))
    kwargs['state'] = reason
    kwargs['description'] = self.event_list[reason]
    self.service_status = kwargs
    self.fire_event(self.name,**kwargs)

  def logmsg(self,msg):
    for l in msg:
      self.log(l)

  def debug(self,msg):
    if self.debugmode:
      self.log(msg)

  def set_timer(self,cb,timeout):
    if self.timer is not None:
      self.cancel_timer(self.timer)
    if timeout is not None:
      self.timer = self.run_in(cb,timeout)

  def get_group(self,group):
    groupitem = self.get_state(group,"all");
    entity_list = groupitem['attributes']['entity_id']
    return entity_list

  def color_temperature_to_value(self, color_temp):    # Doesn't work above 6000K? Why?
    color_temp = str.lower(str(color_temp))

    if(color_temp == "2500" or color_temp == "ultra warm"):
        return 400                 # Ultra Warm - 2500K
    elif(color_temp == "2750" or color_temp == "incandescent"):
        return 363.63              # Incandescent - 2750K
    elif(color_temp == "3000" or color_temp == "warm"):
        return 333.33              # Warm - 3000K
    elif (color_temp == "3200" or color_temp == "neutral warm"):
        return 312.5               # Neutral Warm - 3200K
    elif (color_temp == "3500" or color_temp == "neutral"):
        return 285.71              # Neutral - 3500K
    elif (color_temp == "4000" or color_temp == "cool"):
        return 250                 # Cool - 4000K
    elif (color_temp == "4500" or color_temp == "cool daylight"):
        return 222.22              # Cool Daylight - 4500K
    elif (color_temp == "5000" or color_temp == "soft daylight"):
        return 200                 # Soft Daylight - 5000K
    elif (color_temp == "5500" or color_temp == "daylight"):
        return 181.82              # Daylight - 5500K
    elif (color_temp == "6000" or color_temp == "noon daylight"):
        return 166.67              # Noon Daylight - 6000K
    #elif (color_temp == 6500 or color_temp == "bright daylight"):
    #    return 153.85             # Bright Daylight - 6500K
    #elif (color_temp == 7000 or color_temp == "cloudy daylight"):
    #    return 142.86             # Cloudy Daylight - 7000K
    #elif (color_temp == 7500 or color_temp == "blue daylight"):
    #    return 133.33             # Blue Daylight - 7500K
    #elif (color_temp == 8000 or color_temp == "blue overcast"):
    #    return 125                # Blue Overcast - 8000K
    #elif (color_temp == 8500 or color_temp == "blue water"):
    #    return 117.65             # Blue Water - 8500K
    #elif (color_temp == 9000 or color_temp == "blue ice"):
    #    return 111.11             # Blue Ice - 9000K
    else:
        return 285.71

  def cycle(self, entity, attribute, old, new, kwargs):
    if new != "":
      if self.effect:
        self.debug("Cancelling any outstanding effect")
        self.set_timer(self.effect,None)
        for e in self.lights:
          self.turn_off(e)
        self.effect_state = None
      self.effect_name = new.lower()
      self.debug("In cycle, new="+self.effect_name)
      if self.effect_name != "off":
        self.debug("Calling "+self.effect_name)
        fn = getattr(self, self.effect_name+"_effect", None)
        if fn:
          self.effect = fn
          self.effect(None)
        else:
          self.error("Unknown effect "+self.effect_name)
          return


  def random_effect(self,kwargs):
    for e in self.lights:
      c = random.choice(self.colors)
      self.debug("Light: " + e + " color:" + c)
      self.turn_on(e, brightness=self.brightness,
  #                    color_temp=self.color_temp,
                      color_name=c)

    self.set_timer(self.random_effect,self.speed)

  def pulse_effect(self,kwargs):
    if self.effect_state == None or self.effect_state == True:
      self.effect_state = False
      self.debug("Pulsing on")
      c = random.choice(self.colors)
      for e in self.lights:
        self.debug("Light: " + e + " color:" + c)
        self.turn_on(e, brightness=self.brightness,
                        color_name=c)
    else:
      self.effect_state = True
      for e in self.lights:
        self.debug("Pulsing off "+e)
        self.turn_off(e)

    self.set_timer(self.pulse_effect,self.speed)

  # Just call the strobe and it will do the right thing
  def wave_effect(self,kwargs):
    self.strobe_effect(None)

  def strobe_effect(self,kwargs):
    if self.effect_state == None:
      # Initialize the state machine
      self.effect_state = { 'lights' : self.lights[1:],
                            'color' : random.choice(self.colors),
                            'last' : None,
                            'next' : self.lights[0]
                          }

    self.debug(self.effect_name + " on")
    l = self.effect_state['last']
    n = self.effect_state['next']
    c = self.effect_state['color']
    self.debug("Turning on Light: " + n + " color:" + c)
    self.turn_on(n, brightness=self.brightness,
                    color_name=c)
    # For the strobe effect, we turn off the light behind us
    # For the wave effect, we simply leave it the last color so we skip this
    if l and "strobe" in self.effect_name:
      self.debug("Turning off "+l)
      self.turn_off(l)
    else:
      self.effect_state['color'] = random.choice(self.colors)
    self.effect_state['last'] = n
    try:
      # Pop off the first (vs the last) item
      n = self.effect_state['lights'].pop(0)
      self.effect_state['next'] = n
    except IndexError:
      # If we have poped thru 'em all, just reset the list
      self.effect_state['lights'] = self.lights[1:]
      self.effect_state['next'] = self.lights[0]
      self.effect_state['color'] = random.choice(self.colors)

    self.set_timer(self.strobe_effect,self.speed/2)
