import json

# Path to the JSON file
json_file_path = "output_probe/commonlii__myca/2006/1.json"

# Load and print the "full_text" field
try:
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        if "full_text" in data:
            print(data["full_text"])
        else:
            print("The field 'full_text' does not exist in the JSON file.")
except FileNotFoundError:
    print(f"File not found: {json_file_path}")
except json.JSONDecodeError:
    print("Error decoding JSON file.")
