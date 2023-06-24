from libraries.classes.model import Model
import random
import numpy as np

class Greedy:
    """
    Greedy class constructively generates a schedule by locally taking optimal decisions.
    """

    def __init__(self, empty_model: Model, shuffle=True) -> None:
        """
        Initialize Greedy.

        Args:
            empty_model (Model): empty model to be filled.
            shuffle (bool): to optionally shuffle activities.
        """
        self.model       = empty_model.copy()
        self.activities  = list(self.model.participants.keys())
        self.empty_slots = list(self.model.solution.keys())
        if shuffle:
            self.shuffle_activities()

    def shuffle_activities(self):
        """
        Shuffles list of activities to loop over.
        """
        self.activities = random.sample(self.activities, len(self.activities))

    def get_optimal_index(self, activity: tuple[str, str], current_penalty: int):
        """
        Finds the best index for a given activity based on penalty points.

        Args:
            activity (tuple): activity to find the optimal index for.
            current_penalty (int): penalty points of the current model.

        Returns:
            optimal_index (int): best index found.
            lowest_penalty (int): total penalty after inserting activity at optimal_index.
        """      

        # loop over timeslots
        lowest_penalty = 100000
        for index in self.empty_slots:

            self.model.add_activity(index, activity)
            new_penalty = self.model.total_penalty()

            # if penalty unchanged, optimal index is found
            if new_penalty == current_penalty:
                self.model.remove_activity(index=index)
                return index, current_penalty

            # if penalty lower than best, save index and penalty
            elif new_penalty < lowest_penalty:
                optimal_index  = index
                lowest_penalty = new_penalty

            self.model.remove_activity(index=index)

        return optimal_index, lowest_penalty

    def insert_greedily(self, activity: tuple[str, str], current_penalty):
        """
        Inserts activity greedily.

        Args:
            activity (tuple): activity to be inserted.
            current_penalty (int): total penalty before insertion.

        Returns:
            (int) total penalty after insertion.
        """
        index, penalty = self.get_optimal_index(activity, current_penalty)
        self.model.add_activity(index, activity)
        self.update_empty_slots(index)
        return penalty

    def update_empty_slots(self, index):
        """
        Args:
            index (int): slot that has been filled.
        """
        self.empty_slots.remove(index)

    def run(self) -> Model:
        """
        Runs greedy algorithm once.

        Returns:
            model (Model): the generated solution. 
        """
        current_penalty = 0
        for activity in self.activities:
            current_penalty = self.insert_greedily(activity, current_penalty)
            print('penalty:', current_penalty, end='\r')

        return self.model

class RandomGreedy(Greedy):
    """
    Combines random and greedy choices to contructively generate a schedule.
    """
        
    def insert_randomly(self, activity: tuple[str, str]):
        """
        Inserts activity at random index while considering room size.

        Args:
            activity (tuple): activity to be inserted.

        Returns:
            (int) total penalty after insertion.
        """
        # index = self.model.get_random_index(empty=True)
        overflow = True
        while overflow:
            index = self.model.get_random_index(empty=True)
            overflow = self.capacity_overflow(index, activity)
        added = self.model.add_activity(index, activity)
        self.update_empty_slots(index)
        print(activity, added)
        return self.model.total_penalty()
    
    def capacity_overflow(self, index, activity, max_difference=5):
        """
        Ensures random insertion considers hall size.
        """
        if self.model.capacity_penalty(index, activity) > max_difference:
            return True
        return False

    def calc_random_chance(self, i, start=0.7, alpha=0.064):
        """
        Gives the probability of a random insertion based on a exponential. 

        Args:
            i (int)       : amount of activities inserted. 0 <= i <= 72.
            start (float) : random_chance at i = 0 
            alpha (float) : exponential factor, decides the drop-off speed.

        Returns:
            (float): probability of a random insertion (high at the
                     beginning of the run, lower towards the end).
        """
        return start * np.exp(-alpha * i)

    def run(self):
        """
        Runs random-greedy algorithm once.

        Args:
            random_chance (float): probability of a random insertion.

        Returns:
            model (Model): the generated solution. 
        """
        current_penalty = 0
        for i, activity in enumerate(self.activities):
            
            # make random or greedy choice 
            if random.random() < self.calc_random_chance(i):
                current_penalty = self.insert_randomly(activity)
            else:
                current_penalty = self.insert_greedily(activity, current_penalty)
            
            print(f'penalty: {current_penalty} capacity penalty: {self.model.total_capacity_penalties()} gap penalty: {self.model.student_schedule_penalties()["gap penalties"]}  planned: {self.count_planned_activities()}')#, end='\r')
        
        return self.model