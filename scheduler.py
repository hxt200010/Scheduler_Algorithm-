import argparse
import heapq
from enum import Enum
from queue import PriorityQueue

class EventType(Enum):
    ARRIVE = 0
    START_RUNNING = 1
    TIMER_EXPIRE = 2
    STOP_RUNNING = 3



class Event:
    """Base class for all events in the simulation"""

    def __init__(self, event_type, process, time):
        self.event_type = event_type
        self.process = process
        self.time = time

    def __lt__(self, other):
        return self.time < other.time

class Burst:
    """Class that represents a CPU or I/O burst"""

    def __init__(self, duration, is_cpu=True):
        self.duration = duration
        self.is_cpu = is_cpu


class ArriveEvent(Event):
    """Event that represents a process arrival"""

    def __init__(self, time, process):
        super().__init__(EventType.ARRIVE, process, time)
        self.process = process

    def process(self, sim):
        """Process the arrival event"""
        sim.scheduler.add_process(self.process)


class UnblockEvent(Event):
    """Event that represents a process unblocking"""

    def __init__(self, time, process):
        super().__init__(EventType.STOP_RUNNING, process, time)
        self.process = process

    def process(self, sim):
        """Process the unblock event"""
        sim.scheduler.unblock_process(self.process)

class TimerEvent(Event):
    """Event that represents a timer"""

    def __init__(self, time, process):
        super().__init__(EventType.TIMER_EXPIRE, process, time)

    def process(self, sim):
        """Process the timer event"""
        sim.timer_expired()



class StopRunningEvent(Event):
    """Event that represents a process completing a CPU burst"""

    def __init__(self, time, process):
        super().__init__(EventType.STOP_RUNNING, process, time)
        self.process = process

    def process(self, sim):
        """Process the stop running event"""
        sim.scheduler.complete_burst(self.process)


class Process:
    """Class that represents a simulated process"""

    def __init__(self, pid, bursts, arrival_time):
        self.pid = pid
        self.bursts = bursts
        self.arrival_time = arrival_time
        self.current_burst = 0
        self.start_time = None
        self.finish_time = None
        self.response_time = None
        self.wait_time = None
        self.turnaround_time = None
        self.burst_time = 0

    def is_finished(self):
        """Check if the process has completed all bursts"""
        return self.current_burst >= len(self.bursts)

    def get_next_burst(self):
        """Get the next burst for the process"""
        if self.is_finished():
            return None
        burst = self.bursts[self.current_burst]
        self.current_burst += 1
        self.burst_time = 0
        return burst

    def get_remaining_time(self):
        """Get the remaining time of the current burst"""
        if self.is_finished():
            return 0
        return self.get_next_burst().duration - self.burst_time

    def start(self, start_time):
        """Start the process at the given time"""
        self.start_time = start_time
        self.wait_time = start_time - self.arrival_time

    def complete_burst(self, finish_time):
        """Complete the current burst at the given time"""
        self.finish_time = finish_time
        self.turnaround_time = finish_time - self.arrival_time
        self.burst_time = 0
        self.response_time = self.start_time - self.arrival_time if self.response_time is None else self.response_time

    def block(self, block_time):
        """Block the process for the given time"""
        self.burst_time = 0
        self.response_time = None

    def resume(self, resume_time):
        """Resume the process at the given time"""
        self.wait_time += resume_time - self.finish_time
        self.finish_time = resume_time

    def __str__(self):
        """Return a string representation of the process"""
        service_time = sum(burst.duration for burst in self.bursts)
        avg_response_time = self.response_time/len(self.bursts) if self.response_time is not None else 0
        return f"Process {self.pid}: Arrival Time={self.arrival_time}, Service Time={service_time}, Start Time={self.start_time}, Finish Time={self.finish_time}, Turnaround Time={self.turnaround_time}, Normalized Turnaround Time={self.turnaround_time/service_time}, Average Response Time={avg_response_time}"


class Scheduler:
    """Base class for all scheduling algorithms"""

    def __init__(self):
        self.ready_queue = []

    def add_process(self, process):
        """Add a process to the ready queue"""
        raise NotImplementedError()

    def unblock_process(self, process):
        """Handle a process unblocking"""
        raise NotImplementedError()

    def complete_burst(self, process):
        """Handle a process completing a CPU burst"""
        if process.is_finished():
            if (self.get_estimated_service_time(process), process) in self.ready_queue:
                self.ready_queue.remove((self.get_estimated_service_time(process), process))
        else:
            if (self.get_estimated_service_time(process), process) not in self.ready_queue:
                self.unblock_process(process)

    def get_next_process(self):
        """Get the next process to run"""
        raise NotImplementedError()


class FCFS(Scheduler):
    def __init__(self):
        super().__init__()
        self.ready_queue = []

    def add_process(self, process):
        self.ready_queue.append(process)

    def remove_process(self, process):
        if process in self.ready_queue:
            self.ready_queue.remove(process)

    def ready_queue_empty(self):
        return len(self.ready_queue) == 0

    def get_next_process(self):
        return self.ready_queue[0]

    def handle_event(self, event):
        if event.event_type == EventType.ARRIVE:
            self.add_process(event.process)
        elif event.event_type == EventType.START_RUNNING:
            pass
        elif event.event_type == EventType.TIMER_EXPIRE:
            process = event.process
            process.block(event.time)
            self.add_process(process)
        elif event.event_type == EventType.STOP_RUNNING:
            process = event.process
            process.complete_burst(event.time)
            if process.is_finished():
                self.remove_process(process)
            else:
                self.add_process(process)
        else:
            raise Exception(f"Invalid event type {event.event_type} for FCFS scheduler.")

    def print_statistics(self):
        for process in processes:
            print(str(process))

class RR(Scheduler):
    def __init__(self, quantum):
        super().__init__()
        self.quantum = quantum
        self.ready_queue = []
        self.running_process = None
        self.remaining_time = 0

    def add_process(self, process):
        self.ready_queue.append(process)

    def unblock_process(self, process):
        self.ready_queue.append(process)

    def complete_burst(self, process):
        self.remaining_time = 0
        if process.is_finished():
            self.running_process = None
        else:
            self.unblock_process(process)

    def get_next_process(self):
        if self.running_process is not None and self.remaining_time > 0:
            return self.running_process
        elif len(self.ready_queue) > 0:
            self.running_process = self.ready_queue.pop(0)
            self.remaining_time = min(self.quantum, self.running_process.get_remaining_time())
            return self.running_process
        else:
            return None

    def handle_event(self, event):
        if event.event_type == EventType.ARRIVE:
            self.add_process(event.process)
        elif event.event_type == EventType.START_RUNNING:
            pass
        elif event.event_type == EventType.TIMER_EXPIRE:
            process = event.process
            if self.running_process is None or process == self.running_process:
                self.complete_burst(process)
            else:
                process.block(event.time)
                self.unblock_process(process)
        elif event.event_type == EventType.STOP_RUNNING:
            process = event.process
            process.complete_burst(event.time)
            self.complete_burst(process)
        else:
            raise Exception(f"Invalid event type {event.event_type} for RR scheduler.")

    def print_statistics(self):
        for process in processes:
            print(str(process))

    def ready_queue_empty(self):
        return len(self.ready_queue) == 0 and self.running_process is None

class SPN(Scheduler):
    def __init__(self, alpha, service_given):
        super().__init__()
        self.alpha = alpha
        self.service_given = service_given
        self.ready_queue = []

    def add_process(self, process):
        heapq.heappush(self.ready_queue, (self.get_estimated_service_time(process), process))

    def unblock_process(self, process):
        heapq.heappush(self.ready_queue, (self.get_estimated_service_time(process), process))

    def complete_burst(self, process):
        if process.is_finished():
            if (self.get_estimated_service_time(process), process) in self.ready_queue:
                self.ready_queue.remove((self.get_estimated_service_time(process), process))
        else:
            if (self.get_estimated_service_time(process), process) not in self.ready_queue:
               self.unblock_process(process)

    def get_next_process(self):
        if len(self.ready_queue) == 0:
            return None
        return self.ready_queue[0][1]

    def get_estimated_service_time(self, process):
        if self.service_given:
            return process.bursts[0].duration
        else:
            s1 = process.bursts[0].duration
            st = sum([burst.duration for burst in process.bursts])
            return self.alpha * s1 + (1 - self.alpha) * st

    def handle_event(self, event):
        if event.event_type == EventType.ARRIVE:
            self.add_process(event.process)
        elif event.event_type == EventType.START_RUNNING:
            pass
        elif event.event_type == EventType.TIMER_EXPIRE:
            process = event.process
            if process == self.get_next_process():
                self.complete_burst(process)
            else:
                process.block(event.time)
                self.unblock_process(process)
        elif event.event_type == EventType.STOP_RUNNING:
            process = event.process
            process.complete_burst(event.time)
            self.complete_burst(process)
        else:
            raise Exception(f"Invalid event type {event.event_type} for SPN scheduler.")

    def ready_queue_empty(self):
        return len(self.ready_queue) == 0

    def print_statistics(self):
        for process in processes:
            print(str(process))


def parse_args():
    parser = argparse.ArgumentParser(description='Simulation of various scheduling algorithms')
    parser.add_argument('scheduler_file', type=str, help='File specifying the scheduling algorithm')
    parser.add_argument('process_file', type=str, help='File specifying the processes information to use')
    args = parser.parse_args()
    return args


def load_scheduler(scheduler_file):
    with open(scheduler_file) as f:
        scheduler_type = f.readline().strip()
        if scheduler_type == "FCFS":
            return FCFS()
        elif scheduler_type == "SPN":
            alpha, service_given = map(float, f.readline().split())
            return SPN(alpha, service_given)
        elif scheduler_type == "RR":
            quantum = int(f.readline().strip())
            return RR(quantum)
        else:
            raise Exception(f"Invalid scheduler type {scheduler_type}.")


def load_processes(process_file):
    processes = []
    with open(process_file) as f:
        num_processes = int(f.readline().strip())
        for i in range(num_processes):
            line = f.readline().strip()
            if not line:
                continue  # Skip empty line
            process_id, num_bursts, arrival_time, *burst_info = map(int, line.split())
            bursts = [Burst(duration, is_cpu) for duration, is_cpu in zip(burst_info[::2], burst_info[1::2])]
            processes.append(Process(process_id, bursts, arrival_time))
    return processes


def main():
    args = parse_args()
    scheduler = load_scheduler(args.scheduler_file)
    global processes
    processes = load_processes(args.process_file)
    event_queue = PriorityQueue()
    for process in processes:
        event_queue.put(Event(EventType.ARRIVE, process, process.arrival_time))
    clock = 0
    while not event_queue.empty():
        event = event_queue.get()
        clock = event.time
        scheduler.handle_event(event)
        while not scheduler.ready_queue_empty():
            process = scheduler.get_next_process()
            if not process.start_time:
                process.start(clock)
                event_queue.put(Event(EventType.START_RUNNING, process, clock))
            if process.get_remaining_time() <= 1:
                event_queue.put(Event(EventType.STOP_RUNNING, process, clock + process.get_remaining_time()))
            else:
                event_queue.put(Event(EventType.TIMER_EXPIRE, process, clock + 1))
            break
    scheduler.print_statistics()
    print("Simulation completed.")


if __name__ == '__main__':
    main()