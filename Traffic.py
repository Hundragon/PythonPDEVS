# Import code for DEVS model representation:
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

# Generator class
class Gcar:
    def __init__(self, current="None"):
        self.set(current)
    
    def set(self, value="None"):
        self.__state = value
    
    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()

class GeneratorCar(AtomicDEVS):
    def __init__(self, name=None):
        AtomicDEVS.__init__(self, name)
        self.state = Gcar("None")
        self.gen_outport = self.addOutPort("gen_outport")

    def timeAdvance(self):
        print(f"GeneratorCar timeAdvance: state = {self.state.get()}")
        state = self.state.get()
        if state == 'None':
            return 5
        elif state == 'generate':
            return 0.0
        else:
            raise DEVSException("unknown state <%s> in Generator time advance transition function" % state)
        
    def intTransition(self):
        print(f"GeneratorCar intTransition: current state = {self.state.get()}")
        state = self.state.get()

        if state == "None":
            print("GeneratorCar state: None -> generate")
            return Gcar("generate")
        elif state == "generate":
            print("GeneratorCar state: generate -> None")
            return Gcar("None")
        else:
            raise DEVSException("unknown state <%s> in Generator internal transition function" % state)
    
    def outputFnc(self):
        print(f"GeneratorCar outputFnc: state = {self.state.get()}")
        state = self.state.get()
        if state == "generate":
            print("GeneratorCar output: new_car")
            return {self.gen_outport: "new_car"}
        else:
            return {self.gen_outport: "None"}

# Buffer class
class TrafficLightStorage:
    def __init__(self):
        self.state = 'Yellow'  # Initial state
        self.queue = []  # Queue for cars waiting to be processed

    def extTransition(self, input_value):
        if input_value == 'new_car':
            self.queue.append(input_value)
            self.state = 'Red'  # Transition to Red when a new car arrives
        self.updateState()

    def intTransition(self):
        self.updateState()

    def updateState(self):
        if not self.queue:
            self.state = 'Green'  # Transition to Green momentarily after processing a car
        elif self.queue:
            self.state = 'Red'  # Remain Red if queue is not empty and cars are waiting

    def processCar(self):
        if self.queue:
            self.queue.pop(0)  # Process the first car in the queue
            self.state = 'Green'  # Transition to Green momentarily after processing a car
            self.updateState()
    
    def queue_empty(self):
        return len(self.queue)==0

    def getState(self):
        return self.state

class TrafficLightMode:
    """
    Encapsulates the system's state
    """
    # Yellow when queue not exist
    def __init__(self, current="Yellow"):
        self.set(current)

    def set(self, value="Yellow"):
        self.__colour = value

    def get(self):
        return self.__colour

    def __str__(self):
        return self.get()

class TrafficLight(AtomicDEVS):
    def __init__(self, name=None):
        AtomicDEVS.__init__(self, name)
        self.buffer = TrafficLightStorage()  # Initialize TrafficLightStorage
        self.state = TrafficLightMode("Yellow")
        self.buffer_in = self.addInPort(name="ADDQUEUE")
        self.buffer_out = self.addOutPort(name="OBSERVED")
        self.state_in = self.addInPort("DELETEQUEUE")

    def extTransition(self, inputs):
        input_value = inputs.get(self.buffer_in)
        state_signal = inputs.get(self.state_in)
        state = self.state.get()
        print(f"TrafficLight extTransition: state = {state}, input_value = {input_value}, state_signal = {state_signal}")

        if input_value == "new_car":
            self.buffer.extTransition(input_value)

        if state == "Yellow" and not self.buffer.queue_empty():
            print("TrafficLight state: Yellow -> Red")
            return TrafficLightMode("Red")
        elif state == "Red" and state_signal == "Ready":
            print("TrafficLight state: Red -> Green")
            return TrafficLightMode("Green")
        else:
            return self.state

    def intTransition(self):
        state = self.state.get()
        print(f"TrafficLight intTransition: current state = {state}")

        if state == "Green":
            if self.buffer.queue_empty():
                print("TrafficLight state: Green -> Yellow (no cars in buffer)")
                return TrafficLightMode("Yellow")
            else:
                self.buffer.processCar()
                return TrafficLightMode("Red")
        elif state == "Yellow":
            return TrafficLightMode("Yellow")
        elif state == "Red":
            return TrafficLightMode("Red")
        else:
            raise DEVSException(f"Unknown state <{state}> in TrafficLight internal transition function")

    def outputFnc(self):
        state = self.state.get()
        print(f"TrafficLight outputFnc: state = {state}")

        if state in ["Yellow", "Red"]:
            return {self.buffer_out: "None"}
        elif state == "Green":
            out = self.buffer.getState()
            print(f"TrafficLight green output: {out}")
            if out is None:
                return {self.buffer_out: "None"}
            else:
                return {self.buffer_out: out}
        else:
            raise DEVSException(f"Unknown state <{state}> in TrafficLight output function")

    def timeAdvance(self):
        state = self.state.get()
        print(f"TrafficLight timeAdvance: state = {state}")
        if state == "Yellow":
            return INFINITY
        elif state == "Red":
            return INFINITY  # Wait for policeman's signal
        elif state == "Green":
            return 1.0  # Allow one car to pass
        else:
            raise DEVSException(f"Unknown state <{state}> in Traffic Light time advance transition function")
# Processor class
class PolicemanMode:
    """
    Encapsulates the Policeman's state
    """
    def __init__(self, current="Ready"):
        self.set(current)

    def set(self, value="Ready"):
        self.__mode = value

    def get(self):
        return self.__mode

    def __str__(self):
        return self.get()
    
class Policeman(AtomicDEVS):
    def __init__(self, name=None):
        AtomicDEVS.__init__(self, name)
        self.proc_in = self.addInPort("proc_in")
        self.proc_out = self.addOutPort("proc_out")
        self.state = PolicemanMode("Ready")

    def extTransition(self, inputs):
        print("Enter Policeman_extTransition")
        proc_in = inputs[self.proc_in]
        print(f"Policeman extTransition: proc_in = {proc_in}, state = {self.state.get()}")
        state = self.state.get()

        if proc_in == "Red":  # If the light is Red, cars are waiting to be processed
            if state == 'Ready':
                print("Policeman state: Ready -> Busy")
                return PolicemanMode("Busy")
            else:
                return PolicemanMode(state)
        else:
            return PolicemanMode(state)

    def intTransition(self):
        print("Enter Policeman_intTransition")
        state = self.state.get()
        print(f"Policeman intTransition: current state = {state}")

        if state == "Busy":
            print("Policeman state: Busy -> Ready")
            return PolicemanMode("Ready")
        elif state == "Ready":
            return PolicemanMode("Ready")
        else:
            raise DEVSException(f"Unknown state <{state}> in Policeman internal transition function")

    def outputFnc(self):
        state = self.state.get()
        print(f"Policeman outputFnc: state = {state}")
        if state == "Ready":
            print("Policeman OutputFnc:", state)
            return {self.proc_out: "Ready"}
        elif state == "Busy":
            print("Policeman outputFnc:", state)
            return {self.proc_out: "Busy"}
        else:
            raise DEVSException(f"Unknown state <{state}> in Policeman output function")

    def timeAdvance(self):
        state = self.state.get()
        print(f"Policeman timeAdvance: state = {state}")
        if state == "Ready":
            return 1 
        elif state == "Busy":
            return 15
        else:
            raise DEVSException(f"Unknown state <{state}> in Policeman time advance function")
        


        
# BP coupled model class
class TrafficSystem(CoupledDEVS):
    def __init__(self, name=None):
        CoupledDEVS.__init__(self, name)
        print("Enter TrafficSystem")
        
        self.policeman = self.addSubModel(Policeman(name="policeman"))
        self.trafficLight = self.addSubModel(TrafficLight(name="trafficLight"))
        self.TrafficSystem_in = self.addInPort(name="TrafficSystem_in")

        self.connectPorts(self.TrafficSystem_in, self.trafficLight.buffer_in)
        print("success to connect [TrafficSystem_in] -> [TrafficLight.buffer_in]")
        self.connectPorts(self.trafficLight.buffer_out, self.policeman.proc_in)
        print("success to connect [TrafficLight.buffer_out] -> [policeman.proc_in]")
        self.connectPorts(self.policeman.proc_out, self.trafficLight.state_in)
        print("success to connect [policeman.proc_out] -> [TrafficLight.state_in]")

    def select(self, immChildren):
        if self.trafficLight in immChildren:  # Prioritize TrafficLight over Policeman
            return self.trafficLight
        else:
            return self.policeman

# G_BP coupled model class
class G_BPmodel(CoupledDEVS):
    def __init__(self, name=None):
        CoupledDEVS.__init__(self, name)
        print("Enter G_BP model")
        self.generator = self.addSubModel(GeneratorCar(name="GeneratorCar"))
        self.TrafficSystem = self.addSubModel(TrafficSystem(name="TrafficSystem"))

        self.connectPorts(self.generator.gen_outport, self.TrafficSystem.TrafficSystem_in)
        print("success to connect [gen_outport] -> [TrafficSystem_in]")

    def select(self, imm):
        if self.generator in imm:
            return self.generator
        elif self.TrafficSystem in imm:
            return self.TrafficSystem