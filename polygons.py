import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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
        points[point_id] = coord  # coord is [x, y, z]
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

def generate_pdf_polygons(xml_file):
    root = parse_xml(xml_file)
    points = get_points(root)
    lines = get_lines(root, points)
    polygons = get_polygons(root, lines)

    c = canvas.Canvas("polygons_output.pdf", pagesize=letter)
    width, height = letter

    # Set a scaling factor to fit the polygons on the page
    scale_factor = 0.01  # Adjust as needed

    # Apply an offset if needed
    x_offset = 50  # Horizontal offset
    y_offset = 50  # Vertical offset

    # Drawing polygons
    for polygon_id, polygon_data in polygons.items():
        path = polygon_data['path']
        if path and len(path) >= 3:  # A valid polygon requires at least 3 points

            # Project 3D points onto 2D plane (e.g., ignore Z-coordinate or use perspective projection)
            projected_points = []
            for coord in path:
                x = coord[0] * scale_factor + x_offset
                y = height - (coord[1] * scale_factor + y_offset)  # Invert Y-axis for PDF coordinate system
                projected_points.append((x, y))

            # Create a path object
            p = c.beginPath()
            p.moveTo(*projected_points[0])
            for point in projected_points[1:]: 
                p.lineTo(*point)
            p.close()

            # Draw the polygon (no fill color)
            c.setStrokeColorRGB(0, 0, 0)  # Black lines
            c.drawPath(p, stroke=1, fill=0)

            # Calculate the center of the polygon
            center_x = sum([point[0] for point in projected_points]) / len(projected_points)
            center_y = sum([point[1] for point in projected_points]) / len(projected_points)

            # Add polygon ID text in the center of the polygon
            c.setFont("Helvetica", 10)
            c.drawString(center_x, center_y, polygon_id)

    c.showPage()
    c.save()

# Example usage:
xml_file = 'C:/Users/yasee/Downloads/705 Cordova Ln, Lenoir City, TN 37771, USA.xml'
generate_pdf_polygons(xml_file)
