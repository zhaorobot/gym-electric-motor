from gym_electric_motor.physical_systems.solvers import EulerSolver
import warnings
import numpy as np

class VoltageSupply:
    """
    Base class for all VoltageSupplies to be used in a SCMLSystem.

    Parameter:
        supply_range(Tuple(float,float)): Minimal and maximal possible value for the voltage supply.
        u_nominal(float): Nominal supply voltage
    """

    #: Minimum and Maximum values of the Supply Voltage.
    supply_range = ()

    @property
    def u_nominal(self):
        """
        Returns:
             float: Nominal Voltage of the Voltage Supply
        """
        return self._u_nominal

    def __init__(self, u_nominal, **__):
        """
        Args:
            u_nominal(float): Nominal voltage of the Voltage Supply.
        """
        self._u_nominal = u_nominal

    def reset(self):
        """
        Reset the voltage supply to an initial state.
        This method is called at every reset of the physical system.

        Returns:
            float: The initial supply voltage.
        """
        return self.get_voltage(0, 0)

    def get_voltage(self, t, i_sup, *args, **kwargs):
        """
        Get the supply voltage based on the floating supply current i_sup, the time t and optional further arguments.

        Args:
            i_sup(float): Supply current floating into the system.
            t(float): Current time of the system.

        Returns:
             list(float): Supply Voltage at time t.
        """
        raise NotImplementedError


class IdealVoltageSupply(VoltageSupply):
    """
    Ideal Voltage Supply that supplies with u_nominal independent of the time and the supply current.
    """

    def __init__(self, u_nominal=600.0, **__):
        # Docstring of superclass
        super().__init__(u_nominal)
        self.supply_range = (u_nominal, u_nominal)

    def get_voltage(self, *_, **__):
        # Docstring of superclass
        return [self._u_nominal]


class RCVoltageSupply(VoltageSupply):
    """Voltage supply modeled as RC element"""
    
    def __init__(self, u_nominal=600.0, supply_parameter=None, **__):
        """
        This Voltage Supply is a model of a non ideal Voltage supply where the ideal voltage source U_0 is part of an RC element
        Args:
            supply_parameter(dict): Consists of Resistance R in Ohm and Capacitance C in Farad
        Additional notes:
            If the product of R and C get too small the numerical stability of the ODE is not given anymore
            typical time differences tau are only in the range of 10e-3. One might want to consider R*C as a
            time constant. The resistance R can be considered as a simplified inner resistance model.
        """
        super().__init__(u_nominal)
        supply_parameter = supply_parameter or {'R': 1, 'C': 4e-3}
        # Supply range is between 0 - capacitor completely unloaded - and u_nominal - capacitor is completely loaded
        assert 'R' in supply_parameter.keys(), "Pass key 'R' for Resistance in your dict"
        assert 'C' in supply_parameter.keys(), "Pass key 'C' for Capacitance in your dict"
        self.supply_range = (0,u_nominal) 
        self._r = supply_parameter['R']
        self._c = supply_parameter['C']
        if self._r*self._c < 1e-4:
            warnings.warn("The product of R and C might be too small for the correct calculation of the supply voltage. You might want to consider R*C as a time constant.")
        self._u_sup = [u_nominal]
        self._u_0 = u_nominal
        self._solver = EulerSolver()
        self._solver.set_system_equation(self.system_equation)
        
    def system_equation(self, t, u_sup, u_0, i_sup, r, c):
        # ODE for derivate of u_sup
        return np.array([(u_0 - u_sup[0] - r*i_sup)/(r*c)])

    def reset(self):
        # Docstring of superclass
        # On reset the capacitor is loaded again
        self._solver.set_initial_value(np.array([self._u_0]))
        self._u_sup = [self._u_0]
        return self._u_sup
    
    def get_voltage(self, t,i_sup):
        # Docstring of superclass
        self._solver.set_f_params(self._u_0, i_sup, self._r, self._c)
        self._u_sup = self._solver.integrate(t)
        return self._u_sup
    
class AC1PhaseSupply(VoltageSupply):
    
    def __init__(self, u_nominal=230, supply_parameter=None, **__):
        super().__init__(u_nominal)
        supply_parameter = supply_parameter or {'frequency': 50, 'phase': np.random.rand()*2*np.pi, 'fixed_phase': False}
        assert 'frequency' in supply_parameter.keys(), "Pass key 'frequency' for frequency f in Hz in your dict"
        assert 'phase' in supply_parameter.keys(), "Pass key 'phase' for the starting phase in in your dict"
        assert 'fixed_phase' in supply_parameter.keys(), "Pass key 'fixed_phase' as Boolean to indicate whether the phase given by the user should be used for every episode"
        assert type(supply_parameter['fixed_phase']) == type(True), "Value for key 'fixed_phase' should be Boolean"
        self._fixed_phi = supply_parameter['fixed_phase']
        self._f = supply_parameter['frequency']
        self._phi = supply_parameter['phase']
        self.supply_range = [-1*self._u_nominal, self._u_nominal]
        
    def reset(self):
        if not self._fixed_phi:
            self._phi = np.random.rand()*2*np.pi
        return self.get_voltage(0)
    
    def get_voltage(self, t, *_, **__):
        # Docstring of superclass
        self._u_sup = [self._u_nominal*np.sqrt(2)*np.sin(self._f*t + self._phi)]
        return self._u_sup

class AC3PhaseSupply(VoltageSupply):
    
    def __init__(self, u_nominal=400, supply_parameter=None, **__):
        super().__init__(u_nominal)
        supply_parameter = supply_parameter or {'frequency': 50, 'phase': np.random.rand()*2*np.pi, 'fixed_phase': False}
        assert 'frequency' in supply_parameter.keys(), "Pass key 'frequency' for frequency f in Hz in your dict"
        assert 'phase' in supply_parameter.keys(), "Pass key 'phase' for the starting phase in in your dict"
        assert 'fixed_phase' in supply_parameter.keys(), "Pass key 'fixed_phase' as Boolean to indicate whether the phase given by the user should be used for every episode"
        assert type(supply_parameter['fixed_phase']) == type(True), "Value for key 'fixed_phase' should be Boolean"
        self._fixed_phi = supply_parameter['fixed_phase']
        self._f = supply_parameter['frequency']
        self._phi = supply_parameter['phase']
        self.supply_range = [-1*self._u_nominal, self._u_nominal]
        
    def reset(self):
        # Docstring of superclass
        if not self._fixed_phi:
            self._phi = np.random.rand()*2*np.pi
        return self.get_voltage(0)
    
    def get_voltage(self, t, *_, **__):
        # Docstring of superclass
        self._u_sup = [self._u_nominal/np.sqrt(3)*np.sqrt(2)*np.sin(self._f*t + self._phi + 2/3*np.pi*i) for i in range(3)]
        return self._u_sup
 
    
