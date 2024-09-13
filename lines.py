import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import itertools
import numpy as np

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
    print(f"line id: {line_id}, linepath: {line_path}")
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

def get_faces(root, polygons):
    faces = {}
    
    for face in root.findall('.//FACES/FACE'):
        face_id = face.attrib.get('ID')
        
        polygon_element = face.find('POLYGON')
        if polygon_element is not None:
            polygon_id = polygon_element.attrib.get('ID')
            
            if polygon_id in polygons:
                faces[face_id] = polygons[polygon_id]
                print(f"Face ID: {face_id} linked to Polygon ID: {polygon_id}")
            else:
                print(f"Warning: Polygon ID {polygon_id} not found for Face ID {face_id}.")
        else:
            print(f"Warning: No POLYGON found within FACE ID {face_id}.")
        
    return faces

def generate_colors(num_colors):
    """Generate a list of colors."""
    return [colors.Color(*np.random.rand(3)) for _ in range(num_colors)]

def generate_pdf(xml_file):
    root = parse_xml(xml_file)
    points = get_points(root)
    lines = get_lines(root, points)
    polygons = get_polygons(root, lines, points)
    faces = get_faces(root, polygons)

    c = canvas.Canvas("linesoutputs.pdf", pagesize=letter)
    width, height = letter
    
    # Set a smaller scaling factor
    scale_factor = 0.01 # Further reduce the scale to fit the lines on the page

    # Apply an offset if needed (start drawing at a higher/lower position)
    x_offset = 50  # Horizontal offset
    y_offset = 200  # Vertical offset

    # Define a base set of colors
    base_palette = [
        colors.red,
        colors.green,
        colors.blue,
        colors.yellow,
        colors.orange,
        colors.purple,
        colors.cyan,
        colors.magenta
    ]
    
    # Extract unique materials from lines
    materials = set(line_data['type'] for line_data in lines.values())
    print(materials)  # Print unique materials for debugging

    # Generate enough colors for the materials
    if len(materials) > len(base_palette):
        colors_needed = len(materials)
        additional_colors = generate_colors(colors_needed - len(base_palette))
        color_palette = base_palette + additional_colors
    else:
        color_palette = base_palette[:len(materials)]
    
    # Create a color map for each material
    material_color_map = dict(zip(materials, itertools.cycle(color_palette)))
    
    # Dictionary to store the labels for each material
    material_labels = {}

    for line_id, line_data in lines.items():
        path = line_data['path']
        if path:
            # Set color based on material
            material = line_data['type']  # Assuming type is used for material here
            color = material_color_map.get(material, colors.black)
            c.setStrokeColor(color)
            c.setLineWidth(1)
            
            # Draw the line with scaling and offset
            for i in range(len(path) - 1):
                x1 = path[i][0] * scale_factor + x_offset
                y1 = height - (path[i][1] * scale_factor + y_offset)
                x2 = path[i + 1][0] * scale_factor + x_offset
                y2 = height - (path[i + 1][1] * scale_factor + y_offset)
                
                c.line(x1, y1, x2, y2)
            
            # Store material label info for corner placement
            if material not in material_labels:
                material_labels[material] = color
    
    # Add material labels in the corners of the PDF
    c.setFillColor(colors.blue)
    y_pos = height - 30  # Starting y position for material labels
    
    for material, color in material_labels.items():
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.rect(width - 150, y_pos, 140, 20, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.drawString(width - 140, y_pos + 5, f"{material}")
        y_pos -= 25  # Move down for next label
    
    # Draw a simple debugging line across the middle of the page
    c.setStrokeColor(colors.red)
    c.line(0, height / 2, width, height / 2)
    
    c.showPage()
    c.save()

# Example usage:
xml_file = 'C:/Users/yasee/Downloads/705 Cordova Ln, Lenoir City, TN 37771, USA.xml'
generate_pdf(xml_file)
