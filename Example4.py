import random
import numpy as np
import streamlit as st
import pandas as pd

class Timetable:
    def __init__(self, num_courses, num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels):
        self.num_courses = num_courses
        self.num_days = num_days
        self.num_timeslots = num_timeslots
        self.num_panels = num_panels
        self.courses = courses
        self.frequencies = frequencies
        self.timetable = np.zeros((num_panels, num_days, num_timeslots), dtype=int)
        self.course_count = {course_id: 0 for course_id in range(1, num_courses + 1)}
        self.fixed_timeslots = fixed_timeslots

        # Validate and place fixed sessions in the timetable
        for item in fixed_timeslots:
            if len(item) == 4:
                panel, day, timeslot, course_id = item
                if 0 <= panel < self.num_panels and 0 <= day < self.num_days and 0 <= timeslot < self.num_timeslots:
                    if course_id in self.course_count:
                        self.timetable[panel][day][timeslot] = course_id
                        self.course_count[course_id] += 1
                    else:
                        print(f"Warning: Invalid course_id {course_id} in fixed_timeslots")
                else:
                    print(f"Warning: Invalid index in fixed_timeslots item {item}")
            else:
                print(f"Warning: Fixed timeslot item should be a tuple of 4 elements, but got {item}")

    def is_feasible(self, course_id, panel, day, start_timeslot):
        # Check if the course can be placed in consecutive slots without gaps
        for timeslot in range(start_timeslot, start_timeslot + self.frequencies[course_id]):
            if timeslot >= self.num_timeslots or self.timetable[panel][day][timeslot] != 0:
                return False
        return True

    def add_course(self, course_id, panel, day):
        start_timeslot = 0
        while start_timeslot <= self.num_timeslots - self.frequencies[course_id]:
            if self.is_feasible(course_id, panel, day, start_timeslot):
                # Place the course in consecutive slots
                for timeslot in range(start_timeslot, start_timeslot + self.frequencies[course_id]):
                    self.timetable[panel][day][timeslot] = course_id
                self.course_count[course_id] += 1
                return True
            start_timeslot += self.frequencies[course_id]
        return False

    def fitness(self):
        conflicts = 0
        for panel in range(self.num_panels):
            for day in range(self.num_days):
                scheduled_courses = set()
                for timeslot in range(self.num_timeslots):
                    course_id = self.timetable[panel][day][timeslot]
                    if course_id != 0:
                        if course_id in scheduled_courses:
                            conflicts += 1  # Conflict: course scheduled more than once in a day
                        scheduled_courses.add(course_id)
        # Penalize if the course is not scheduled exactly the required number of times
        for course_id, count in self.course_count.items():
            if count < self.frequencies[course_id]:
                conflicts += abs(count - self.frequencies[course_id])
        return -conflicts

    def to_dataframe(self, panel):
        # Define days and time slots
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        time_slots = ['08:30-09:30', '09:30-10:30', '10:30-10:45', '10:45-11:45',
                      '11:45-12:45', '12:45-01:30', '01:30-02:30', '02:30-03:30',
                      '03:30-03:45', '03:45-04:45', '04:45-05:45']

        # Create DataFrame from timetable matrix
        df = pd.DataFrame(self.timetable[panel], columns=time_slots, index=days)
    
        def map_courses(x):
            if x == 0:
                return ''
            elif 1 <= x <= len(self.courses):
                return self.courses[x]
            else:
                return 'Invalid'

        # Apply the mapping to each element in the DataFrame
        df = df.applymap(map_courses)
        return df


def create_initial_population(pop_size, num_courses, num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels):
    population = []
    for _ in range(pop_size):
        individual = Timetable(num_courses, num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels)
        for course_id in range(1, num_courses + 1):
            assigned = 0
            while assigned < frequencies[course_id]:
                panel = random.randint(0, num_panels - 1)
                day = random.randint(0, num_days - 1)
                if individual.add_course(course_id, panel, day):
                    assigned += 1
        population.append(individual)
    return population

def crossover(parent1, parent2):
    child = Timetable(parent1.num_courses, parent1.num_days, parent1.num_timeslots, parent1.courses, parent1.frequencies, parent1.fixed_timeslots, parent1.num_panels)
    for panel in range(child.num_panels):
        for day in range(child.num_days):
            for timeslot in range(child.num_timeslots):
                if random.random() < 0.5:
                    course_id = parent1.timetable[panel][day][timeslot]
                else:
                    course_id = parent2.timetable[panel][day][timeslot]
                child.timetable[panel][day][timeslot] = course_id
    return child

def mutate(individual, mutation_rate=0.05):
    for panel in range(individual.num_panels):
        for day in range(individual.num_days):
            for timeslot in range(individual.num_timeslots):
                if random.random() < mutation_rate:
                    course_id = random.randint(1, individual.num_courses)
                    if individual.is_feasible(course_id, panel, day, timeslot):
                        for i in range(timeslot, timeslot + individual.frequencies[course_id]):
                            if i < individual.num_timeslots:
                                individual.timetable[panel][day][i] = course_id

def genetic_algorithm(pop_size, num_generations, num_courses, num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels):
    population = create_initial_population(pop_size, num_courses, num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels)
    for generation in range(num_generations):
        new_population = []
        population = sorted(population, key=lambda x: x.fitness(), reverse=True)
        for i in range(0, pop_size, 2):
            parent1, parent2 = population[i], population[i + 1]
            child1 = crossover(parent1, parent2)
            child2 = crossover(parent1, parent2)
            mutate(child1)
            mutate(child2)
            new_population.extend([child1, child2])
        population = new_population
    return population[0]

# Streamlit Interface
st.title('Timetable Scheduling for 11 Panels')

num_panels = 11  # Number of panels
num_days = 6  # Monday to Saturday
num_timeslots = 11  # 8:30 AM to 5:45 PM including breaks

# Input for number of subjects
num_courses = st.number_input('Enter the number of subjects', min_value=1, max_value=20, value=3)

# Input for subject names and their frequency
courses = {}
frequencies = {}
fixed_timeslots = []

# Predefine some fixed sessions (e.g., Lunch, Fixed Classes)
# Fixed session format: (panel_index, day_index, timeslot_index, course_id)
fixed_timeslots.extend([(panel, 5, 0, -1) for panel in range(num_panels)])  # Lunch breaks for each panel

for i in range(num_courses):
    course_name = st.text_input(f'Enter name of subject {i+1}', key=f'course_name_{i}')
    if course_name:
        courses[i + 1] = course_name
        frequency = st.number_input(f'How many days should {course_name} be taken in a week?', min_value=1, max_value=num_days, value=1, key=f'frequency_{i}')
        frequencies[i + 1] = frequency

# Generate and display the timetable
if courses:
    best_timetable = genetic_algorithm(50, 100, len(courses), num_days, num_timeslots, courses, frequencies, fixed_timeslots, num_panels)
    for panel in range(num_panels):
        st.write(f"Panel {panel + 1}")
        timetable_df = best_timetable.to_dataframe(panel)
        st.dataframe(timetable_df)
        
        # Button to download the timetable as CSV
        csv = timetable_df.to_csv(index=True)
        st.download_button(
            label=f"Download Panel {panel + 1} Timetable as CSV",
            data=csv,
            file_name=f"panel_{panel + 1}_timetable.csv",
            mime='text/csv',
        )
else:
    st.write("Please enter the subject names.")
