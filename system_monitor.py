import paramiko
import psutil
from concurrent.futures import ThreadPoolExecutor

# Define function to get system resource usage locally
def get_local_system_usage():
    try:
        # Get CPU usage as a percentage
        cpu_usage = psutil.cpu_percent(interval=1)

        # Get Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        return 'Local System', cpu_usage, memory_usage
    except Exception as e:
        return 'Local System', f"Error: {e}", None

# Function to run a command on a remote machine via SSH
def get_remote_system_usage(host, username, password):
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password)

        # Run CPU usage command
        stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_output = stdout.read().decode()

        # Extract CPU usage (idle and subtract from 100 to get usage)
        cpu_idle = float(cpu_output.split('%')[0].split()[-1])
        cpu_usage = 100 - cpu_idle

        # Run Memory usage command
        stdin, stdout, stderr = client.exec_command("free -m")
        memory_output = stdout.read().decode()
        memory_data = memory_output.split('\n')[1].split()

        total_memory = float(memory_data[1])
        used_memory = float(memory_data[2])
        memory_usage = (used_memory / total_memory) * 100

        client.close()

        return host, cpu_usage, memory_usage

    except Exception as e:
        return host, f"Error: {e}", None

# Monitor systems (both local and remote)
def monitor_systems(systems):
    with ThreadPoolExecutor(max_workers=10) as executor:
        # List of tasks
        tasks = [executor.submit(get_local_system_usage)]
        
        # Add remote system monitoring tasks
        for system in systems:
            host, username, password = system
            tasks.append(executor.submit(get_remote_system_usage, host, username, password))

        # Display results
        for task in tasks:
            host, cpu_usage, memory_usage = task.result()
            print(f"Host: {host}")
            if isinstance(cpu_usage, str):
                print(cpu_usage)
            else:
                print(f"  CPU Usage: {cpu_usage}%")
                print(f"  Memory Usage: {memory_usage}%")
            print("-" * 30)

# List of systems to monitor (host, username, password)
systems = [
    ('192.168.1.10', 'user1', 'password1'),
    ('192.168.1.11', 'user2', 'password2'),
]

# Call the monitor function
monitor_systems(systems)
