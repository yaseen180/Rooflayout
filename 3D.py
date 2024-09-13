import xml.etree.ElementTree as ET
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import itertools

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
        points[point_id] = coord
        print(f"Point ID: {point_id}, Coordinates: {coord}")
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

def get_polygons(root, lines):
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
        
        # Create a list to store the ordered path of points
        ordered_path = []

        # Create a set to keep track of used lines to avoid duplicates
        used_lines = set()

        # Start with the first line
        if polygon_path:
            first_line_id = polygon_path[0]
            if first_line_id in lines:
                first_line_points = lines[first_line_id]['path']
                ordered_path.extend(first_line_points)
                used_lines.add(first_line_id)
            else:
                print(f"Warning: Line ID {first_line_id} not found in lines dictionary.")

        # Build the ordered path by finding connected lines
        while len(ordered_path) > 0 and len(used_lines) < len(polygon_path):
            last_point = ordered_path[-1]
            found_next = False

            for line_id in polygon_path:
                if line_id in used_lines:
                    continue
                if line_id in lines:
                    line_points = lines[line_id]['path']
                    if line_points[0] == last_point:
                        # The line starts where the previous one ended, add it directly
                        ordered_path.extend(line_points[1:])  # Avoid duplicating the first point
                        used_lines.add(line_id)
                        found_next = True
                        break
                    elif line_points[-1] == last_point:
                        # The line ends where the previous one ended, reverse it before adding
                        ordered_path.extend(line_points[-2::-1])  # Reverse and avoid duplicating the last point
                        used_lines.add(line_id)
                        found_next = True
                        break
            if not found_next:
                print(f"Warning: No continuation found for point {last_point}. Check polygon path for polygon ID {polygon_id}.")
                break

        # Close the polygon by adding the first point to the end if not already closed
        if ordered_path and ordered_path[0] != ordered_path[-1]:
            ordered_path.append(ordered_path[0])

        polygons[polygon_id] = {
            'path': ordered_path,
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

def generate_colors(num_colors):
    """Generate a list of random colors."""
    return [np.random.rand(3,) for _ in range(num_colors)]

def plot_3d_polygons(xml_file):
    root = parse_xml(xml_file)
    points = get_points(root)
    lines = get_lines(root, points)
    polygons = get_polygons(root, lines)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    materials = set(polygon_data['material'] for polygon_data in polygons.values())
    print(materials)  # Print unique materials for debugging

    base_palette = [
        (1, 0, 0),  # red
        (0, 1, 0),  # green
        (0, 0, 1),  # blue
        (1, 1, 0),  # yellow
        (1, 0.5, 0),  # orange
        (0.5, 0, 0.5),  # purple
        (0, 1, 1),  # cyan
        (1, 0, 1)  # magenta
    ]

    if len(materials) > len(base_palette):
        colors_needed = len(materials)
        additional_colors = generate_colors(colors_needed - len(base_palette))
        color_palette = base_palette + additional_colors
    else:
        color_palette = base_palette[:len(materials)]
    
    material_color_map = dict(zip(materials, itertools.cycle(color_palette)))
    
    for polygon_id, polygon_data in polygons.items():
        path = polygon_data['path']
        if path and len(path) >= 3:  # A valid polygon requires at least 3 points
            material = polygon_data['material']
            color = material_color_map.get(material, (0, 0, 0))
            
            poly_path = np.array(path)
            ax.add_collection3d(Poly3DCollection([poly_path], facecolors=color, linewidths=1, edgecolors='r', alpha=.25))

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    
    plt.show()

# Example usage:
xml_file = 'C:/Users/yasee/Downloads/705 Cordova Ln, Lenoir City, TN 37771, USA.xml'
plot_3d_polygons(xml_file)
