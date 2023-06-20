from libraries.classes.student import Student
from libraries.classes.course import Course
from libraries.classes.hall import Hall
from libraries.helpers.load_data import load_courses, load_students, load_halls
from typing import Optional, Union
import copy
import random

activity_type = tuple[str, str]


class Model:
    """A model representation for a schedule.

    Contains methods for manipulation of data in schedule indices and manipulation of members of activities.

    Attributes:
        courses (dict[str, Course]): A mapping of a course name to a Course object.
        students (dict[str, Student]): A mapping of a student index (based on loading order) to a Student object.
        halls (dict[str, Hall]): A mapping of a hall index (based on loading order) to a Hall object.
        solution (dict[int, tuple[str, str]]): A mapping of a schedule slot index
            (which maps to day-timeslot-hall) to an activity. An activity is represented as ('Course name', 'Activity').
            Example of an activity: ('Heuristieken 1', 'lecture 1').
        participants (dict[tuple[str, str], set[int]]): A dictionary containing activities and their set of students
            students are represented by their index number.
    """

    def __init__(self, path: str = "data", auto_load_students: bool = True) -> None:
        """Initiatizes a model for a schedule.

        Args:
            path (str): Path for data to load. Defaults to "data".
            auto_load_students (bool): evaluate if  students have to be added to
                their respective activities in initialisation. Defaults to True.
        """
        self.courses: dict[str, Course] = load_courses(path)
        self.students: dict[int, Student] = load_students(self.courses, path)
        self.halls: dict[int, Hall] = load_halls(path)
        self.solution: dict[int, activity_type] = self.init_model((None, None))
        self.participants = self.init_student_model()
        self.index_penalties: dict[int, int] = self.init_model(0)
        self.student_penalties: dict[int, list[Union[int, set[int]]]] = {}

        if auto_load_students is True:
            # Add members to activities in self.participants.
            self.add_all_students()

    def init_model(self, dict_value) -> dict[int, int | tuple[str, str]]:
        """Initiate a string representation of a schedule.

        Returns:
            dict[int : dict(str, str)]: Index (0 - 144) mapping to a dict containing course and activity.
                Example: {0: {'course': 'Heuristieken', 'activity': 'lecture 1'},
                {1: {'course': None, 'activity': None}, etc.}
        """
        schedule_model: dict[int, int | activity_type] = {
            index: dict_value for index in range((7 * 4 + 1) * 5)
        }

        return schedule_model

    def translate_index(self, index: int) -> dict[str, int]:
        """Return index value as day, timeslot and hall indices.

        Args:
            index (int): Value 0-144 mapping to a day-hall-timeslot combination.
        """
        day = index // 29
        timeslot = (index % 29) // 7
        if (index % 29) == 28:
            # Evening slot exception.
            hall = 5
        else:
            # Regular hall indexing.
            hall = (index % 29) % 7

        return {"day": day, "timeslot": timeslot, "hall": hall}

    def init_student_model(self) -> dict[tuple[str, str], set[int]]:
        """Initiate an activity mapping to a set of students.

        Activities are structured as a tuple('Heuristieken', 'lecture 1').

        Returns:
            dict[tuple[str, str], set[str]]:
                Activity (as unique tuple of course-activity) and a set of student indices.
        """
        participants: dict[tuple[str, str], set[int]] = {}
        for course in self.courses.values():
            for activity in course.activities():
                participants.update({(course.name, activity.category): set()})

        return participants

    def add_all_students(self) -> None:
        """Add all students to activities."""
        for activity_tuple in self.participants:
            for student in self.students:
                self.add_student(int(student), activity_tuple)

    def get_random_index(self, empty: bool = False) -> int:
        """Return random empty index in the schedule.

        Args:
            empty (bool): Flag if random index contains nothing.
                Defaults to false.
        """
        while True:
            # Acquire index independent of content in index.
            index = random.choice(list(self.solution.keys()))
            if empty is False:
                # Return first found index if slot content is irrelevant.
                return index
            if self.check_index_is_empty(index) and empty is True:
                return index

    def check_index_is_empty(self, index: int) -> bool:
        """Return a boolean indicating if index slot contains a course-activity pair."""
        return self.solution[index][0] is None

    def swap_activities(self, index_1, index_2) -> None:
        """Swap activities stored at two indices.

        Args:
            index_1 (int): Index of first activity to be swapped.
            index_2 (int): Index of second activity to be swapped.
        """
        self.solution[index_1], self.solution[index_2] = (
            self.solution[index_2],
            self.solution[index_1],
        )

    def add_activity(self, index: int, activity: tuple[str, str]) -> bool:
        """Add activity to given index in schedule model.

        Returns:
            bool: True if activity was succesfully added, else False.
        """
        if self.check_index_is_empty(index) is True:
            self.solution[index] = activity
            return True
        else:
            return False

    def remove_activity(
        self,
        activity: Optional[activity_type] = None,
        index: Optional[int] = None,
    ) -> bool:
        """Remove activity from the schedule model.

        Activities are structured as tuple("course name", "lecture 1).

        If only activity is given, index is searched and activity is removed at found index.
        If only index is given, activity at specified index is removed.
        If both are given, given activity is compared to stored activity before removal.

        Args:
            activity (tuple[str, str]): course name, activity type.
                Example: ("Heuristieken", "lecture 1)
            index (int): Index in schedule, ranging from 0 - 144.

        Returns:
            bool: True if activity was succesfully removed,
                False if nothing to remove or given activity does not match stored activity.
        """
        if activity is not None and index is not None:
            # Check if stored activity and index match stored information.
            check_index = self.get_index(activity)
            check_activity = self.get_activity(index)

            if check_index == index and check_activity == activity:
                # Remove activity from stored index.
                self.solution[index] = (None, None)
                return True
            else:
                return False

        elif activity is not None:
            # Remove activity from stored index.
            index = self.get_index(activity)
            self.solution[index] = (None, None)
            return True

        elif index is not None:
            # Remove activity from stored index.
            self.solution[index] = (None, None)
            return True

        return False

    def get_hall_capacity(self, index: int) -> int:
        """Return capacity of the hall that is represented by index."""
        # Translate index into information
        info = self.translate_index(index)
        # Get the hall that is described by index
        hall_index = info["hall"]
        # Return hall capacity by from list
        return self.halls[hall_index].capacity

    def get_activity_capacity(self, activity: tuple[str, str]) -> int:
        """Return the capacity of an activity.

        If activity is None, return zero.
        """
        # Start with capacity 0
        capacity = 0
        # Extract course name and type from activity
        course_name = activity[0]
        type = activity[1]

        if course_name and type:
            # Find the course object the activity belongs to
            course = self.courses[course_name]
            # Combine all course activities in one list
            all_activities = course.lectures + course.practicals + course.tutorials

            # Iterate over all Activity objects
            for object in all_activities:
                # If type matches Activity category
                if type == object.category:
                    # Set capacity
                    capacity = object.capacity

            return int(capacity)
        else:
            # If activity is None, return 0
            return 0

    def get_index(self, activity: tuple[str, str]) -> int:
        """Return index of activity in model.

        Args:
            activity (tuple[str, str]): ('course name', 'lecture 1')
        """
        return {
            index for index in self.solution if self.solution[index] == activity
        }.pop()

    def get_activity(self, index: int) -> activity_type:
        """Return activity stored at index in model.

        Args:
            index (int): Value ranging from 0 - 144
        """
        return self.solution[index]

    def student_in_course(self, student: int, course) -> bool:
        """ "Return bool if student in specified course."""
        return True if student in self.courses[course].students else False

    def add_student(self, student: int, activity: tuple[str, str]) -> bool:
        """Add student to an activity in the model.

        Args:
            student (int): Index id of a student.
            activity (tuple[str, str]) : tuple("course name", "lecture 1)

        Returns:
            bool: True if student not in activity yet, False otherwise.
        """
        if student not in self.participants[activity] and self.student_in_course(
            student, activity[0]
        ):
            self.participants[activity].add(student)
            return True
        else:
            return False

    def remove_student(self, student: int, activity: tuple[str, str]) -> bool:
        """Remove student from an activity in the model.

        Args:
            student (int): Index id of a student.
            activity (tuple[str, str]) : tuple("course name", "lecture 1)

        Returns:
            bool: True if student succesfully removed from activity, False otherwise.
        """
        if student in self.participants[activity]:
            self.participants[activity].remove(student)
            return True
        else:
            return False

    def student_activities(self, student: int) -> dict[int, tuple[str, str]]:
        """Return a dict of schedule and activities of the student.

        Example: {0: (Heuristieken, lecture 1), 1: (Algoritmes, werkcollege 1)}

        Args:
            student (int): Index id of the student.
        """
        activities = [
            activity
            for activity, student_list in self.participants.items()
            if student in student_list
        ]
        activity_and_indices: dict[int, tuple[str, str]] = {
            index: activity
            for index, activity in self.solution.items()
            if activity in activities
        }
        return activity_and_indices

    def get_highest_penalties(self, n: int) -> list[dict[int, tuple[str, str]]]:
        """Form a list of activities with highest contributions to penalty points.

        The list of elements is ordered from activities causing most to least penalty points.
        The activities are stored in a dict mapping from their index to the activity.

        Args:
            n (int): length of the list to return.

        Returns:
            list[dict[int, tuple[str, str]]]: A list of {index: activity}
                E.g. {0: ('Heuristieken': 'lecture 1')}.
        """

        # Update self.index_penalties.
        self.total_penalty()

        # Find the highest penalties stored.
        highest_penalties = []
        model = self.index_penalties
        highest_values = sorted(model.values(), reverse=True)[:n]

        for high_value in highest_values:
            for index, value in model.items():
                if value == high_value:
                    activity = self.get_activity(index)
                    highest_penalties.append({index: activity})

        return highest_penalties

    def get_highest_students(self, n) -> list[int]:
        """Search the model for students in activities with highest penalties.

        Returns a list of length n where each element is the student_index of a
        student that caused a high penalty. The first element (list[0])
        is the activty with the highest penalty and the last element (list[n]) is the
        activity with the lowest penalty.

        Returns:
            list[int]:
        """
        self.total_penalty()

        highest_penalties = []
        # Take the student penalty model

        return print("LET OP !!!get_highest_students(self, n) werkt nog niet !!")

    def capacity_penalty(self, index: int, activity: tuple[str, str]) -> int:
        """Return the capacity penalty for an activity over capacity.

        Args:
            index (int): Index of the activity in the model.
            activity (tuple[str, str]): Activity to check,
                an activity is a tuple of ('course name', 'activity').

         Returns:
            int: Penalty points for each student over capacity. 0 if there is no penalty.
        """
        # Get capacity for the activity and the location.
        hall_capacity = self.get_hall_capacity(index)
        activity_capacity = self.get_activity_capacity(activity)

        if activity_capacity > hall_capacity:
            # Return penalty points for each student over capacity.
            return activity_capacity > hall_capacity
        # Return no penalty points.
        return 0

    def total_capacity_penalties(self) -> int:
        """Check the capacity penalty per if the number of students of each activity exceeds
        the hall capacity.For every student that doesn't fit 1 penalty
        point is counted. the total capacity penalty is returned (int).
        The function also keeps track of the model in self.index_penalties."""

        penalty_points = 0

        # Iterate over all indices in model
        for index, activity in self.solution.items():
            index_penalty = self.capacity_penalty(index, activity)
            penalty_points += index_penalty
            self.index_penalties[index] += index_penalty

        # print("capacity penalty:", penalty_points)
        return penalty_points

    def evening_penalty(self) -> int:
        """Calculate penalties of activities in evening slot.
        Fills in empty model with {index: penalty}.
        returns total evening penalty."""

        # Start with 0 penalty points, set evening penalty to 5
        penalty_points = 0
        evening_penalty = 5

        # Iterate over indices and activities in model
        for index, activity in self.solution.items():
            # If index is mapped to activity
            if activity[0]:
                # Get info on index
                info = self.translate_index(index)
                # Check if activity is in evening slot
                if info["timeslot"] == 4:
                    # If so, add penalty points
                    penalty_points += evening_penalty
                    self.index_penalties[index] += evening_penalty

        # print("evening penalty:", penalty_points)
        return penalty_points

    def conflict_penalty(self) -> int:
        """Calculate the penalties of students with course conflicts.
        Fills in empty student activity model {activity: {student_id: penalty}}.
        returns total conflict penalty. The function also keeps track of the model in
        self.student_penalties."""

        penalty_points = 0

        # Iterate over students
        for id in self.students:
            # Variable for previous activities of student
            prev_slots = []
            # Total penalty points of student
            student_penalty = 0
            # Get all activities from student
            activities = self.student_activities(id)
            # Iterate over activites
            for activity in activities:
                # Get info on activity
                info = self.translate_index(activity)
                # Save day-timeslot
                temp = (info["timeslot"], info["day"])
                # Check if day-timeslot was already used for other activity
                if temp in prev_slots:
                    # If so, update student penalty and total penalty
                    student_penalty += 1
                    penalty_points += 1
                    # If student is not in student penalty model
                    if id not in self.student_penalties.keys():
                        # Add student to model
                        self.student_penalties.update(
                            {id: [student_penalty, {activity}]}
                        )
                    # If student already in model
                    else:
                        # Update student penalty and add activity index
                        self.student_penalties[id][0] = student_penalty
                        self.student_penalties[id][1].add(activity)
                # If day-timeslot not used
                else:
                    # add to previous slot variable
                    prev_slots.append(temp)

        # print("conflict penalty: ", penalty_points)

        return penalty_points

    def schedule_gaps_penalty(self) -> int:
        """Calculate The function also keeps track of the model in
        self.student_penalties."""
        return 0

    def total_penalty(self) -> int:
        """Calculate the total penalty of the schedule.

        return: penalty (int)"""
        total = (
            self.total_capacity_penalties()
            + self.evening_penalty()
            + self.conflict_penalty()
            + self.schedule_gaps_penalty()
        )

        return total

    def copy(self) -> "Model":
        new_copy = copy.copy(self)
        new_copy.solution = copy.copy(self.solution)
        new_copy.participants = copy.deepcopy(self.participants)

        return new_copy

    def student_has_valid_schedule(self, student: int) -> bool:
        try:
            activities = self.student_activities(student)
            indices = [
                activity
                for activity in self.solution.values()
                if activity in activities.values()
            ]
            dict(zip(indices, activities, strict=True))
        except ValueError:
            return False

        return True

    def is_solution(self) -> bool:
        if self.student_has_valid_schedule(261) is False:
            return False

        # compare with set
        n_activities = 0
        for course in self.courses.values():
            n_activities += len(course.activities())

        activity_set = set()
        for activity in self.solution.values():
            activity_set.add(activity)

        if n_activities <= len(activity_set):
            return True
        else:
            return False
