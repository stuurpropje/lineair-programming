import random
import math
from libraries.algorithms.hillclimber import HillClimber
from libraries.classes.model import Model


class SimulatedAnnealing(HillClimber):
    """
    The SimulatedAnnealing class that changes a random node in the model to a random valid value.
    Each improvement or equivalent solution is kept for the next iteration.
    Also sometimes accepts solutions that are worse, depending on the current temperature.

    Most of the functions are similar to those of the HillClimber class, which is why
    we use that as a parent class.
    """

    def __init__(self, model: Model, temperature: int or float = 1):
        # Use the init of the Hillclimber class
        super().__init__(model)

        # Starting temperature and current temperature
        self.T0 = temperature
        self.T = temperature

    def update_temperature(self) -> None:
        """
        This function implements a *linear* cooling scheme.
        Temperature will become zero after all iterations passed to the run()
        method have passed.
        """
        self.T = self.T - (self.T0 / self.iterations)

        # Exponential would look like this:
        # alpha = 0.99
        # self.T = self.T * alpha

        # where alpha can be any value below 1 but above 0

    def check_solution(self, new_model: Model) -> None:
        """
        Checks and accepts better solutions than the current solution.
        Also sometimes accepts solutions that are worse, depending on the current
        temperature.
        """
        new_value = new_model.total_penalty()
        old_value = self.penalties

        # Calculate the probability of accepting this new solution
        delta = new_value - old_value
        probability = math.exp(-delta / self.T)

        # NOTE: Keep in mind that if we want to maximize the value, we use:
        # delta = old_value - new_value

        # Pull a random number between 0 and 1 and see if we accept the soltuion!
        if random.random() < probability:
            self.schedule = new_model
            self.penalties = new_value

        # Update the temperature
        self.update_temperature()