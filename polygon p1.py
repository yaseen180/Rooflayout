import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

def get_points(root):
    points = {}
    for point in root.findall('.//POINTS/POINT'):
        point_id = point.attrib['ID']
        data = point.attrib['DATA']
        coord = list(map(float, data.split(',')))
        if len(coord) >= 2:
            points[point_id] = coord[:2]  # Take only the first two coordinates (x, y)
            print(f"Point ID: {point_id}, Coordinates: {coord[:2]}")
        else:
            print(f"Warning: Point ID {point_id} does not have enough coordinates.")
    return points

def get_lines(root, points):
    lines = {}
    for line in root.findall('.//LINES/LINE'):
        line_id = line.attrib['ID']
        line_path = line.attrib['PATH'].split(',')
        line_type = line.attrib['TYPE']
        line_length = float(line.attrib['LENGTH'])
        line_uom = line.attrib['UOM']
        line_pitch = line.attrib['PITCH']
        pitch = list(map(float, line_pitch.split(',')))
        line_pitch_uom = line.attrib['PITCHUOM']
        line_storey = line.attrib['STOREY']
        
        line_points = []
        for point_id in line_path:
            if point_id in points:
                line_points.append(points[point_id])
            else:
                print(f"Warning: Point ID {point_id} not found in points dictionary.")
        
        lines[line_id] = {
            'path': line_points,
            'type': line_type,
            'length': line_length,
            'uom': line_uom,
            'pitch': pitch,
            'pitch_uom': line_pitch_uom,
            'storey': line_storey
        }
        print(f"Line ID: {line_id}, Line Path: {line_path}")
    return lines

def get_polygons(root, lines, points):
    polygons = {}
    for polygon in root.findall('.//FACES/FACE/POLYGON'):
        polygon_id = polygon.attrib['ID']
        polygon_path = polygon.attrib['PATH'].split(',')
        polygon_size = float(polygon.attrib['SIZE'])
        polygon_sizeuom = polygon.attrib['SIZEUOM']
        polygon_pitch = float(polygon.attrib['PITCH'])
        polygon_pitchuom = polygon.attrib['PITCHUOM']
        polygon_orientation = polygon.attrib['ORIENTATION']
        polygon_type = polygon.attrib['TYPE']
        polygon_mat = polygon.attrib['MAT']
        polygon_storey = polygon.attrib['STOREY']
        
        path_lines = []
        for line_id in polygon_path:
            if line_id in lines:
                path_lines.extend(lines[line_id]['path'])
            else:
                print(f"Warning: Line ID {line_id} not found in lines dictionary.")

        polygons[polygon_id] = {
            'path': path_lines,
            'size': polygon_size,
            'size_uom': polygon_sizeuom,
            'pitch': polygon_pitch,
            'pitch_uom': polygon_pitchuom,
            'orientation': polygon_orientation,
            'type': polygon_type,
            'material': polygon_mat,
            'storey': polygon_storey
        }
        print(f"Polygon ID: {polygon_id}, Polygon Path: {polygon_path}")
    return polygons

def plot_all_polygons_2d(xml_file):
    root = parse_xml(xml_file)
    points = get_points(root)
    lines = get_lines(root, points)
    polygons = get_polygons(root, lines, points)

    fig, ax = plt.subplots()
    
    for polygon_id, polygon_data in polygons.items():
        path = polygon_data['path']
        if path:
            # Extract x and y coordinates
            x_coords = [pt[0] for pt in path]
            y_coords = [pt[1] for pt in path]
            
            # Close the polygon by appending the first point at the end
            x_coords.append(x_coords[0])
            y_coords.append(y_coords[0])
            
            # Plot polygon path
            ax.plot(x_coords, y_coords, marker='o', linestyle='-', color='b', label=f'Polygon {polygon_id}')
            ax.fill(x_coords, y_coords, color='lightblue', alpha=0.5)
            
            # Annotate all points used in the polygon path
            for point_id, coord in points.items():
                if coord in path:
                    x, y = coord
                    ax.text(x, y, point_id, fontsize=9, ha='right', color='black')
    
    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_title('2D Plot of All Polygons with Points')
    plt.grid(True)
    plt.legend(loc='best')
    plt.show()

# Example usage:
xml_file = 'C:/Users/yasee/Downloads/189 Home Pl Ct SE, Cleveland, TN 37323, USA.xml'
plot_all_polygons_2d(xml_file)
