# Copyright 2014 Modelling, Simulation and Design Lab (MSDL) at 
# McGill University and the University of Antwerp (http://msdl.cs.mcgill.ca/)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

# Import code for DEVS model representation:
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class TrafficLightMode:
    """
    Encapsulates the system's state
    """

    def __init__(self, current="red"):
        """
        Constructor (parameterizable).
        """
        self.set(current)

    def set(self, value="red"):
        self.__colour=value

    def get(self):
        return self.__colour

    def __str__(self):
        return self.get()

class TrafficLight(AtomicDEVS):
    """
    A traffic light 
    """
  
    def __init__(self, name=None):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
    
        # STATE:
        #  Define 'state' attribute (initial sate):
        self.state = TrafficLightMode("red") 

        # ELAPSED TIME:
        #  Initialize 'elapsed time' attribute if required
        #  (by default, value is 0.0):
        self.elapsed = 1.5 
        # with elapsed time initially 1.5 and initially in 
        # state "red", which has a time advance of 60,
        # there are 60-1.5 = 58.5time-units  remaining until the first 
        # internal transition 
    
        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.INTERRUPT = self.addInPort(name="INTERRUPT")
        self.OBSERVED = self.addOutPort(name="OBSERVED")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        # Compute the new state 'Snew' based (typically) on current
        # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
        input = inputs.get(self.INTERRUPT)

        state = self.state.get()

        if input == "toManual":
            if state == "manual":
                # staying in manual mode
                return TrafficLightMode("manual")
            elif state in ("red", "green", "yellow"):
                return TrafficLightMode("manual")
        elif input == "toAutonomous":
            if state == "manual":
                return TrafficLightMode("red")
            elif state in ("red", "green", "yellow"):
                # If toAutonomous is given while still autonomous, just stay in this state
                return self.state
        raise DEVSException(\
            "unknown state <%s> in TrafficLight external transition function"\
            % state) 

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state == "red":
            return TrafficLightMode("green")
        elif state == "green":
            return TrafficLightMode("yellow")
        elif state == "yellow":
            return TrafficLightMode("red")
        else:
            raise DEVSException(\
                "unknown state <%s> in TrafficLight internal transition function"\
                % state)
  
    def outputFnc(self):
        """
        Output Funtion.
        """
   
        # A colourblind observer sees "grey" instead of "red" or "green".
 
        # BEWARE: ouput is based on the OLD state
        # and is produced BEFORE making the transition.
        # We'll encode an "observation" of the state the
        # system will transition to !

        # Send messages (events) to a subset of the atomic-DEVS' 
        # output ports by means of the 'poke' method, i.e.:
        # The content of the messages is based (typically) on current State.
 
        state = self.state.get()

        if state == "red":
            return {self.OBSERVED: "grey"}
        elif state == "green":
            return {self.OBSERVED: "yellow"}
        elif state == "yellow":
            return {self.OBSERVED: "grey"}
        else:
            raise DEVSException(\
                "unknown state <%s> in TrafficLight external transition function"\
                % state)
    
    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state == "red":
            return 60 
        elif state == "green":
            return 50 
        elif state == "yellow":
            return 10 
        elif state == "manual":
            return INFINITY 
        else:
            raise DEVSException(\
                "unknown state <%s> in TrafficLight time advance transition function"\
                % state)

class PolicemanMode:
    """
    Encapsulates the Policeman's state
    """
    def __init__(self, current="idle"):
        """
        Constructor (parameterizable).
        """
        self.set(current)

    def set(self, value="idle"):
        self.__mode=value

    def get(self):
        return self.__mode

    def __str__(self):
        return self.get()

class Policeman(AtomicDEVS):
    """
    A policeman producing "toManual" and "toAutonomous" events:
    "toManual" when going from "idle" to "working" mode
    "toAutonomous" when going from "working" to "idle" mode
    """
    def __init__(self, name=None):
        """
        Constructor (parameterizable).
        """
    
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
    
        # STATE:
        #  Define 'state' attribute (initial sate):
        self.state = PolicemanMode("idle") 

        # ELAPSED TIME:
        #  Initialize 'elapsed time' attribute if required
        #  (by default, value is 0.0):
        self.elapsed = 0 
    
        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.OUT = self.addOutPort(name="OUT")

    def intTransition(self):
        """
        Internal Transition Function.
        The policeman works forever, so only one mode. 
        """
  
        state = self.state.get()

        if state == "idle":
            return PolicemanMode("working")
        elif state == "working":
            return PolicemanMode("idle")
        else:
            raise DEVSException(\
                "unknown state <%s> in Policeman internal transition function"\
                % state)
    
    def outputFnc(self):
        """
        Output Funtion.
        """
        # Send messages (events) to a subset of the atomic-DEVS' 
        # output ports by means of the 'poke' method, i.e.:
        # The content of the messages is based (typically) on current State.
        state = self.state.get()
        if state == "idle":
            return {self.OUT: "toManual"}
        elif state == "working":
            return {self.OUT: "toAutonomous"}
        else:
            raise DEVSException(\
                "unknown state <%s> in Policeman output function"\
                % state)
    
    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
    
        state = self.state.get()

        if state == "idle":
            return 200 
        elif state == "working":
            return 100 
        else:
            raise DEVSException(\
                "unknown state <%s> in Policeman time advance function"\
                % state)

class TrafficSystem(CoupledDEVS):
    def __init__(self, name=None):
        """
        A simple traffic system consisting of a Policeman and a TrafficLight.
        """
        # Always call parent class' constructor FIRST:
        CoupledDEVS.__init__(self, name)

        # Declare the coupled model's output ports:
        # Autonomous, so no output ports

        # Declare the coupled model's sub-models:

        # The Policeman generating interrupts 
        self.policeman = self.addSubModel(Policeman(name="policeman"))

        # The TrafficLight 
        self.trafficLight = self.addSubModel(TrafficLight(name="trafficLight"))

        # Only connect ...
        self.connectPorts(self.policeman.OUT, self.trafficLight.INTERRUPT)

    def select(self, immChildren):
        """
        Choose a model to transition from all possible models.
        """
        # Policeman has priority over the traffic light
        if self.policeman in immChildren:
            return self.policeman
        else:
            # Doesn't really matter, as they don't influence each other
            return immChildren[0]
