from backend.python.Target import Target
from backend.python.const import DAY
from backend.python.enums import Shape, Mobility
from backend.python.Time import Time
from backend.python.location.Building import Building
from backend.python.location.Location import Location
from backend.python.transport.Movement import Movement
import numpy as np

from backend.python.transport.Walk import Walk


class CommercialCanteen(Building):
    def get_suggested_sub_route(self, point, t, force_dt=False):
        if force_dt:
            _r = [Target(
                self,
                t+np.random.randint(1, min(np.random.uniform(Time.get_duration(0.25), Time.get_duration(0.5)), DAY - t)),
                None)]
        else:
            _r = [Target(
                self,
                np.random.randint(Time.get_time_from_dattime(11, 0), Time.get_time_from_dattime(17, 30)),
                None)]

        t = Time.get_current_time(_r, t)
        return _r, t

    def __init__(self, shape: Shape, x: float, y: float, name: str, exittheta=0.0, exitdist=0.9, infectiousness=1.0,
                 **kwargs):
        super().__init__(shape, x, y, name, exittheta, exitdist, infectiousness, **kwargs)
