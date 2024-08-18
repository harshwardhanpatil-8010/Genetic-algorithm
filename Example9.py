import streamlit as st
import prettytable as prettytable
import random as rnd
from datetime import datetime, timedelta

# Constants
POPULATION_SIZE = 9
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.1

# University Time Constants
UNIVERSITY_START_TIME = datetime.strptime("08:30", "%H:%M")
UNIVERSITY_END_TIME = datetime.strptime("17:45", "%H:%M")
LUNCH_BREAK_START = datetime.strptime("12:45", "%H:%M")
LUNCH_BREAK_END = datetime.strptime("13:30", "%H:%M")
TIME_SLOT_DURATION = timedelta(hours=1)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Room Class
class Room:
    def __init__(self, number):
        self._number = number

    def get_number(self):
        return self._number

# Instructor Class
class Instructor:
    def __init__(self, id, name):
        self._id = id
        self._name = name

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

# Course Class
class Course:
    def __init__(self, number, name, instructors, lectures_per_week):
        self._number = number
        self._name = name
        self._instructors = instructors
        self._lectures_per_week = lectures_per_week

    def get_number(self):
        return self._number

    def get_name(self):
        return self._name

    def get_instructors(self):
        return self._instructors

    def get_lectures_per_week(self):
        return self._lectures_per_week

# Department Class
class Department:
    def __init__(self, name, courses):
        self._name = name
        self._courses = courses

    def get_name(self):
        return self._name

    def get_courses(self):
        return self._courses

# MeetingTime Class
class MeetingTime:
    def __init__(self, id, day, time):
        self._id = id
        self._day = day
        self._time = time

    def get_id(self):
        return self._id

    def get_day(self):
        return self._day

    def get_time(self):
        return self._time

# Panel Class
class Panel:
    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

# Data Class (Storage)
class Data:
    def __init__(self):
        self._rooms = []
        self._meeting_times = []
        self._instructors = []
        self._courses = []
        self._depts = []
        self._panels = []

    def add_room(self, room):
        self._rooms.append(room)

    def add_meeting_time(self, meeting_time):
        self._meeting_times.append(meeting_time)

    def add_instructor(self, instructor):
        self._instructors.append(instructor)

    def add_course(self, course):
        self._courses.append(course)

    def add_dept(self, dept):
        self._depts.append(dept)

    def add_panel(self, panel):
        self._panels.append(panel)

    def get_rooms(self):
        return self._rooms

    def get_meeting_times(self):
        return self._meeting_times

    def get_instructors(self):
        return self._instructors

    def get_courses(self):
        return self._courses

    def get_depts(self):
        return self._depts

    def get_panels(self):
        return self._panels

    def generate_meeting_times(self):
        meeting_time_id = 1
        for day in DAYS_OF_WEEK:
            current_time = UNIVERSITY_START_TIME
            while current_time < UNIVERSITY_END_TIME:
                if current_time < LUNCH_BREAK_START or current_time >= LUNCH_BREAK_END:
                    meeting_time = MeetingTime(f'MT{meeting_time_id}', day, current_time.strftime("%H:%M"))
                    self.add_meeting_time(meeting_time)
                    meeting_time_id += 1
                current_time += TIME_SLOT_DURATION

# Schedule Class (Genetic Algorithm)
class Schedule:
    def __init__(self, data, panel):
        self._data = data
        self._panel = panel
        self._classes = []
        self._fitness = 0
        self._is_fitness_changed = True

    def get_classes(self):
        self._is_fitness_changed = True
        return self._classes

    def initialize(self):
        self._classes = []
        for dept in self._data.get_depts():
            for course in dept.get_courses():
                for _ in range(course.get_lectures_per_week()):
                    meeting_time = rnd.choice(self._data.get_meeting_times())
                    room = rnd.choice(self._data.get_rooms())
                    instructor = rnd.choice(course.get_instructors()) if course.get_instructors() else None
                    if instructor:
                        self._classes.append({
                            "panel": self._panel.get_name(),
                            "department": dept.get_name(),
                            "course": course.get_name(),
                            "room": room.get_number(),
                            "instructor": instructor.get_name(),
                            "meeting_time": f"{meeting_time.get_day()} {meeting_time.get_time()}"
                        })
        return self

    def get_fitness(self):
        if self._is_fitness_changed:
            self._fitness = self.calculate_fitness()
            self._is_fitness_changed = False
        return self._fitness

    def calculate_fitness(self):
        room_time_slots = set()
        instructor_time_slots = set()

        for cls in self._classes:
            room_time_slot = (cls["room"], cls["meeting_time"])
            instructor_time_slot = (cls["instructor"], cls["meeting_time"])

            if room_time_slot in room_time_slots or instructor_time_slot in instructor_time_slots:
                return 0.0  # Penalize for conflicts

            room_time_slots.add(room_time_slot)
            instructor_time_slots.add(instructor_time_slot)

        # Example fitness calculation: Higher if more classes are scheduled without conflicts
        return len(self._classes) / (len(self._data.get_rooms()) * len(DAYS_OF_WEEK))

# Population Class (Genetic Algorithm)
class Population:
    def __init__(self, size, data):
        self._schedules = [Schedule(data, panel).initialize() for panel in data.get_panels()]

    def get_schedules(self):
        return self._schedules

# Genetic Algorithm Class
class GeneticAlgorithm:
    def evolve(self, population):
        new_schedules = []
        schedules = population.get_schedules()

        # Elitism: Keep the best schedules
        sorted_schedules = sorted(schedules, key=lambda s: s.get_fitness(), reverse=True)
        new_schedules.extend(sorted_schedules[:NUMB_OF_ELITE_SCHEDULES])

        # Selection and crossover
        for _ in range(len(schedules) - NUMB_OF_ELITE_SCHEDULES):
            parent1 = rnd.choice(sorted_schedules[:TOURNAMENT_SELECTION_SIZE])
            parent2 = rnd.choice(sorted_schedules[:TOURNAMENT_SELECTION_SIZE])
            child = self.crossover(parent1, parent2)
            new_schedules.append(child)

        # Mutation
        for schedule in new_schedules:
            if rnd.random() < MUTATION_RATE:
                self.mutate(schedule)

        return Population(POPULATION_SIZE, schedules[0]._data)

    def crossover(self, parent1, parent2):
        child = Schedule(parent1._data, parent1._panel)
        half_len = len(parent1.get_classes()) // 2
        child._classes = parent1.get_classes()[:half_len] + parent2.get_classes()[half_len:]
        return child

    def mutate(self, schedule):
        if schedule.get_classes():
            i, j = rnd.sample(range(len(schedule.get_classes())), 2)
            schedule._classes[i], schedule._classes[j] = schedule._classes[j], schedule._classes[i]

# DisplayManager Class (for Output)
class DisplayManager:
    def print_schedule_as_table(self, schedule):
        table = prettytable.PrettyTable(['Panel', 'Department', 'Course', 'Room', 'Instructor', 'Meeting Time'])
        for cls in schedule.get_classes():
            table.add_row([
                cls["panel"],
                cls["department"],
                cls["course"],
                cls["room"],
                cls["instructor"],
                cls["meeting_time"]
            ])
        st.text(table)

# Streamlit App
def main():
    st.title('Timetable Scheduling using Genetic Algorithm')

    # User input
    with st.form(key='input_form'):
        # Adding rooms
        room_numbers = st.text_area('Enter room numbers separated by commas')
        room_numbers = [room.strip() for room in room_numbers.split(',')]
        rooms = [Room(room_number) for room_number in room_numbers]

        # Adding instructors
        instructors_input = st.text_area('Enter instructor names separated by commas')
        instructors = [Instructor(f'I{i}', name.strip()) for i, name in enumerate(instructors_input.split(','))]

        # Adding courses
        course_names = st.text_area('Enter course names separated by commas')
        courses = []
        for i, course_name in enumerate(course_names.split(',')):
            selected_instructors = st.multiselect(f'Select instructors for {course_name.strip()}', instructors, format_func=lambda inst: inst.get_name())
            lectures_per_week = st.number_input(f'Number of lectures per week for {course_name.strip()}', min_value=1)
            courses.append(Course(f'C{i}', course_name.strip(), selected_instructors, lectures_per_week))

        # Adding department
        department_name = st.text_input('Enter department name')
        department = Department(department_name, courses)

        # Adding panels
        panel_names = st.text_area('Enter panel names separated by commas')
        panels = [Panel(panel_name.strip()) for panel_name in panel_names.split(',')]

        # Submit button
        submitted = st.form_submit_button('Submit')

        if submitted:
            # Initialize data
            data = Data()
            for room in rooms:
                data.add_room(room)
            data.generate_meeting_times()
            for instructor in instructors:
                data.add_instructor(instructor)
            for course in courses:
                data.add_course(course)
            data.add_dept(department)
            for panel in panels:
                data.add_panel(panel)

            # Scheduling
            display_manager = DisplayManager()
            population = Population(POPULATION_SIZE, data)
            generation_number = 0

            while population.get_schedules() and any(schedule.get_fitness() != 1.0 for schedule in population.get_schedules()):
                generation_number += 1
                st.write(f"Generation #{generation_number}")
                for schedule in population.get_schedules():
                    display_manager.print_schedule_as_table(schedule)
                population = GeneticAlgorithm().evolve(population)

            # Final schedule
            st.success("Schedule generation complete!")
            if population.get_schedules():
                for schedule in population.get_schedules():
                    display_manager.print_schedule_as_table(schedule)
            else:
                st.error("No valid schedules found!")

if __name__ == "__main__":
    main()
