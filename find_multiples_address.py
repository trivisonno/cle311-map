import geojson
import csv
from collections import defaultdict
from datetime import datetime
import pytz

def parse_geojson(file_path):
    with open(file_path, 'r') as f:
        data = geojson.load(f)
    return data

def format_datetime(ms_epoch):
    # Convert milliseconds since epoch to datetime string in Cleveland time
    cleveland_tz = pytz.timezone('America/New_York')
    dt = datetime.fromtimestamp(ms_epoch / 1000.0, tz=pytz.utc)
    dt_cleveland = dt.astimezone(cleveland_tz)
    return dt_cleveland

def process_case_id(case_id):
    # Disregard the first 7 digits of CaseID
    return case_id[7:] if len(case_id) > 7 else case_id

def extract_features(data):
    features = []

    for feature in data['features']:
        address = feature['properties'].get('Location', '')
        case_id = feature['properties'].get('CaseID', '')
        case_type = feature['properties'].get('CaseType', 'N/A')
        opened_datetime_ms = feature['properties'].get('OpenedDateTime', 0)
        opened_datetime = format_datetime(opened_datetime_ms)
        
        # Process CaseID
        processed_case_id = process_case_id(str(case_id))
        
        feature_info = {
            'CaseID': processed_case_id,
            'Location': address,
            'CaseType': case_type,
            'OpenedDateTime': opened_datetime
        }
        features.append(feature_info)

    # Sort features by OpenedDateTime from oldest to newest
    features_sorted = sorted(features, key=lambda x: x['OpenedDateTime'])

    return features_sorted

def find_addresses_with_multiple_features(data):
    address_features = defaultdict(list)

    for feature in data['features']:
        address = feature['properties'].get('Location', '').lower()
        case_id = feature['properties'].get('CaseID', '')
        case_type = feature['properties'].get('CaseType', 'N/A')
        opened_datetime_ms = feature['properties'].get('OpenedDateTime', 0)
        opened_datetime_str = format_datetime(opened_datetime_ms)
        
        # Process CaseID
        processed_case_id = process_case_id(str(case_id))
        
        feature_info = {
            'CaseID': processed_case_id,
            'CaseType': case_type,
            'OpenedDateTime': opened_datetime_str
        }
        address_features[address].append(feature_info)

    # Filter addresses with more than one feature
    multiple_features = {addr: props for addr, props in address_features.items() if len(props) > 1}

    # Sort addresses by the number of requests (features) in descending order
    sorted_multiple_features = dict(sorted(multiple_features.items(), key=lambda item: len(item[1]), reverse=True))

    return sorted_multiple_features

def write_geojson_file(data, output_file_path, addresses_with_multiple_features):
    # Filter features that are part of addresses with multiple requests
    features = [feature for feature in data['features']
                if feature['properties'].get('Location', '').lower() in addresses_with_multiple_features]
    
    # Write to a new GeoJSON file
    with open(output_file_path, 'w') as f:
        geojson.dump({'type': 'FeatureCollection', 'features': features}, f, indent=2)

def write_text_file(output_file_path, multiple_features):
    with open(output_file_path, 'w') as f:
        # Write total number of addresses with multiple features
        f.write(f"Total addresses with multiple features: {len(multiple_features)}\n\n")

        for address, features in multiple_features.items():
            address_formatted = address.title()  # Capitalize the first letter of each word in the address
            f.write(f"{address_formatted} ({len(features)} requests)\n")
            for feature in features:
                f.write(f"{feature['CaseID']}, {feature['CaseType']}, {feature['OpenedDateTime'].strftime('%B %d, %Y, %I:%M%p')}\n")
            f.write("\n")  # Add a blank line between addresses

def write_csv_file(output_file_path, features):
    with open(output_file_path, 'w', newline='') as csvfile:
        fieldnames = ['CaseID', 'Location', 'CaseType', 'OpenedDateTime']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for feature in features:
            writer.writerow({
                'CaseID': feature['CaseID'],
                'Location': feature['Location'],
                'CaseType': feature['CaseType'],
                'OpenedDateTime': feature['OpenedDateTime'].strftime('%B %d, %Y, %I:%M%p')
            })

def main():
    file_path = '311-2.geojson'
    geojson_data = parse_geojson(file_path)
    features_sorted = extract_features(geojson_data)
    
    # Find addresses with multiple features for GeoJSON and text output
    multiple_features = find_addresses_with_multiple_features(geojson_data)
    
    # Write GeoJSON file with only the features from addresses with multiple requests
    write_geojson_file(geojson_data, 'filtered_features.geojson', multiple_features)
    
    # Write detailed information to a text file
    write_text_file('addresses_w_multiple_requests.txt', multiple_features)
    
    # Write the entire sorted features to a CSV file
    write_csv_file('sorted_features.csv', features_sorted)

if __name__ == "__main__":
    main()