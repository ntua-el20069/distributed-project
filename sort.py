import re

def sort_log_file(input_file_path, output_file_path):
    # Read the file and store the lines
    with open(input_file_path, 'r') as f:
        log_lines = f.readlines()

    # Regular expression to extract (node_i, no_line) pattern from the log
    pattern = r"\(node_(\d+), (\d+)\)"

    # Function to extract (i, no_line) tuple from the log line
    def extract_sort_key(line):
        match = re.search(pattern, line)
        if match:
            # Extract (i, no_line) as integers
            return int(match.group(1)), int(match.group(2))
        return (float('inf'), float('inf'))  # For lines that don't match the pattern

    # Sort the lines using the extracted (i, no_line) as the sorting key
    sorted_lines = sorted(log_lines, key=extract_sort_key)

    # Write the sorted lines to a new file
    with open(output_file_path, 'w') as f:
        f.writelines(sorted_lines)


def sort_log_values(input_file_path, output_file_path):
    # Read the file and store the lines
    with open(input_file_path, 'r') as f:
        log_lines = f.readlines()

    # Regular expression to extract success values from the log
    pattern = r"(success: )([0-9,]+)"

    # Function to sort the values inside the list in the log line
    def sort_values_in_line(line):
        # Search for the pattern
        match = re.search(pattern, line)
        if match:
            # Extract the list of values as a string, split by commas, convert to integers, sort them, and join them back
            values = match.group(2).split(',')
            sorted_values = sorted(map(int, values))
            # Replace the old unsorted values with the sorted ones
            sorted_values_str = ','.join(map(str, sorted_values))
            return line.replace(match.group(2), sorted_values_str)
        return line

    # Sort values within the log lines
    sorted_lines = [sort_values_in_line(line) for line in log_lines]

    # Write the sorted lines back to a new file
    with open(output_file_path, 'w') as f:
        f.writelines(sorted_lines)


# Example usage:
input_file_path = "compare.txt"  # Path to your input file
median_file_path = "sorted_logs.txt"  # Path to output the sorted file
output_file_path = "sorted_compare.txt"  # Path to output the sorted file

sort_log_file(input_file_path, median_file_path)
sort_log_values(median_file_path, output_file_path)
