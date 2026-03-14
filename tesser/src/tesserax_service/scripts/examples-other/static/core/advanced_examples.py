#!/usr/bin/env python3
"""
Advanced Tesserax Examples: Force Layouts, Physics, and Neural Networks

This demonstrates some of the most powerful features of Tesserax including:
1. Force-directed graph layouts
2. Physics simulations with gravity and collisions
3. Neural network visualizations
4. Complex hierarchical layouts
"""

import math
from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Group,
    Point,
    Rect,
    RenderConfig,
    Text,
    ViewportSpec,
    render_batch,
)
from tesserax.layout import ForceLayout, HierarchicalLayout, GridLayout, RowLayout

def force_directed_network():
    """Creates a force-directed graph layout showing network connectivity."""
    print("🌐 Creating force-directed network layout...")
    
    canvas = Canvas(width=1600, height=1200)
    
    # Create nodes for a social network
    nodes = []
    node_labels = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    
    # Create the force layout with nodes
    with ForceLayout(iterations=150, diameter=300) as network:
        for i, name in enumerate(node_labels):
            # Create node with different colors
            hue = (i * 45) % 360
            node = Circle(r=25, fill=f"hsl({hue}, 60%, 75%)", stroke=Colors.DarkBlue, width=2)
            nodes.append(node)
            
        # Define connections (edges) - creating a realistic social network
        connections = [
            (0, 1), (0, 2), (1, 2), (1, 3), (2, 4), 
            (3, 4), (3, 5), (4, 6), (5, 6), (5, 7), (6, 7),
            (0, 4), (2, 6)  # Some cross-connections
        ]
        
        # Add connections to the force layout
        for i, j in connections:
            network.connect(nodes[i], nodes[j])
        # Connections update graph topology, so run layout after wiring edges.
        network.do_layout()
    
    # Add the network to canvas
    canvas.add(network)
    
    # Draw the edges manually after layout is complete
    for i, j in connections:
        start_pos = Point(nodes[i].transform.tx, nodes[i].transform.ty)
        end_pos = Point(nodes[j].transform.tx, nodes[j].transform.ty)
        
        # Calculate edge points on circle boundaries
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Normalize and offset by radius
            norm_dx, norm_dy = dx/dist, dy/dist
            start_edge = Point(
                start_pos.x + norm_dx * 25,
                start_pos.y + norm_dy * 25
            )
            end_edge = Point(
                end_pos.x - norm_dx * 25,
                end_pos.y - norm_dy * 25
            )
            
            edge = Arrow(
                p1=start_edge,
                p2=end_edge,
                stroke=Colors.Gray,
                width=1
            )
            canvas.add(edge)
    
    # Add labels after positioning
    for i, name in enumerate(node_labels):
        node_pos = Point(nodes[i].transform.tx, nodes[i].transform.ty)
        label = Text(name, size=11, fill=Colors.Black, font="sans-serif")
        label.move_to(node_pos)
        canvas.add(label)
    
    return canvas

def hierarchical_tree_layout():
    """Creates a hierarchical tree layout for organizational charts or decision trees."""
    print("🌳 Creating hierarchical tree layout...")
    
    canvas = Canvas(width=1600, height=1200)
    
    # Create nodes for an organizational chart
    nodes = {}
    node_data = {
        "CEO": {"level": 0, "children": ["CTO", "CFO", "COO"]},
        "CTO": {"level": 1, "children": ["DevLead", "QALead"]},
        "CFO": {"level": 1, "children": ["Accounting", "Finance"]},
        "COO": {"level": 1, "children": ["Marketing", "Sales"]},
        "DevLead": {"level": 2, "children": ["Dev1", "Dev2"]},
        "QALead": {"level": 2, "children": ["QA1"]},
        "Accounting": {"level": 2, "children": []},
        "Finance": {"level": 2, "children": []},
        "Marketing": {"level": 2, "children": []},
        "Sales": {"level": 2, "children": ["Sales1", "Sales2"]},
        "Dev1": {"level": 3, "children": []},
        "Dev2": {"level": 3, "children": []},
        "QA1": {"level": 3, "children": []},
        "Sales1": {"level": 3, "children": []},
        "Sales2": {"level": 3, "children": []},
    }
    
    # Create the hierarchical layout
    with HierarchicalLayout(
        orientation="vertical",
        rank_sep=80,
        node_sep=40
    ) as tree:
        
        # Create nodes with different styles based on level
        for name, data in node_data.items():
            level = data["level"]
            
            if level == 0:  # CEO
                node = Rect(w=100, h=40, fill=Colors.Gold, stroke=Colors.DarkRed, width=2)
            elif level == 1:  # Directors
                node = Rect(w=80, h=35, fill=Colors.LightBlue, stroke=Colors.DarkBlue, width=2)
            elif level == 2:  # Managers
                node = Rect(w=70, h=30, fill=Colors.LightGreen, stroke=Colors.DarkGreen, width=2)
            else:  # Individual contributors
                node = Rect(w=60, h=25, fill=Colors.LightGray, stroke=Colors.DarkGray, width=2)
            
            nodes[name] = node
            
            # Set root
            if level == 0:
                tree.root(node)
    
    # Define connections
    for name, data in node_data.items():
        parent_node = nodes[name]
        for child_name in data["children"]:
            child_node = nodes[child_name]
            tree.connect(parent_node, child_node)
    # Recompute layout after all edges are defined.
    tree.do_layout()
    
    canvas.add(tree)
    
    # Add labels to nodes
    for name, node in nodes.items():
        node_pos = Point(node.transform.tx, node.transform.ty)
        label = Text(name, size=10, fill=Colors.Black, font="sans-serif")
        label.move_to(node_pos)
        canvas.add(label)
    
    # Add connecting lines (we'll draw them manually)
    for name, data in node_data.items():
        parent_node = nodes[name]
        parent_pos = Point(parent_node.transform.tx, parent_node.transform.ty)
        parent_bounds = parent_node.local()
        
        for child_name in data["children"]:
            child_node = nodes[child_name]
            child_pos = Point(child_node.transform.tx, child_node.transform.ty)
            child_bounds = child_node.local()
            
            # Draw line from bottom of parent to top of child
            line = Arrow(
                p1=Point(parent_pos.x, parent_pos.y + parent_bounds.height/2),
                p2=Point(child_pos.x, child_pos.y - child_bounds.height/2),
                stroke=Colors.DarkGray,
                width=1
            )
            canvas.add(line)
    
    return canvas

def neural_network_visualization():
    """Creates a neural network architecture visualization with layers."""
    print("🧠 Creating neural network visualization...")
    
    canvas = Canvas(width=1600, height=1200)
    
    # Network architecture: Input(4) -> Hidden1(6) -> Hidden2(4) -> Output(2)
    layer_sizes = [4, 6, 4, 2]
    layer_names = ["Input", "Hidden 1", "Hidden 2", "Output"]
    layer_colors = [Colors.LightBlue, Colors.LightGreen, Colors.LightYellow, Colors.LightCoral]
    
    layers = []
    layer_groups = []
    
    # Create layers using RowLayout for horizontal arrangement
    with RowLayout(gap=120, align="middle") as network:
        for size, name, color in zip(layer_sizes, layer_names, layer_colors):
            # Create a column of neurons for this layer
            layer_neurons = []
            
            with GridLayout(cols=1, gap=20) as layer:
                for _ in range(size):
                    neuron = Circle(r=20, fill=color, stroke=Colors.DarkBlue, width=2)
                    layer_neurons.append(neuron)
            
            layers.append(layer_neurons)
            layer_groups.append((name, layer))
    
    canvas.add(network)

    # Add labels after the layout has finalized layer positions.
    for name, layer in layer_groups:
        layer_label = Text(name, size=14, fill=Colors.Black, font="sans-serif")
        layer_bounds = layer.local()
        layer_pos = Point(layer.transform.tx, layer.transform.ty)
        label_y = layer_pos.y + layer_bounds.height / 2 + 40
        layer_label.move_to(Point(layer_pos.x, label_y))
        canvas.add(layer_label)
    
    # After layout, get actual neuron positions and draw connections
    for layer_idx in range(len(layers) - 1):
        current_layer = layers[layer_idx]
        next_layer = layers[layer_idx + 1]
        
        # Connect every neuron in current layer to every neuron in next layer
        for current_neuron in current_layer:
            current_pos = Point(current_neuron.transform.tx, current_neuron.transform.ty)
            
            for next_neuron in next_layer:
                next_pos = Point(next_neuron.transform.tx, next_neuron.transform.ty)
                
                # Calculate connection points on neuron boundaries
                dx = next_pos.x - current_pos.x
                dy = next_pos.y - current_pos.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 0:
                    norm_dx, norm_dy = dx/dist, dy/dist
                    start_point = Point(
                        current_pos.x + norm_dx * 20,
                        current_pos.y + norm_dy * 20
                    )
                    end_point = Point(
                        next_pos.x - norm_dx * 20,
                        next_pos.y - norm_dy * 20
                    )
                    
                    connection = Arrow(
                        p1=start_point,
                        p2=end_point,
                        stroke=Colors.Gray,
                        width=1
                    )
                    canvas.add(connection)
    
    # Add title
    title = Text("Neural Network Architecture", size=18, fill=Colors.DarkBlue, font="serif")
    title.move_to(Point(400, 50))
    canvas.add(title)
    
    return canvas

def convolutional_operation_demo():
    """Demonstrates a convolutional neural network operation with matrices."""
    print("🔄 Creating convolution operation visualization...")
    
    canvas = Canvas(width=900, height=400)
    
    # Input matrix (5x5)
    input_data = [
        [1, 0, 1, 0, 1],
        [0, 1, 0, 1, 0], 
        [1, 0, 2, 0, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1]
    ]
    
    # Kernel (3x3) 
    kernel_data = [
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ]
    
    # Output (3x3)
    output_data = [
        [4, 3, 4],
        [3, 6, 3],
        [4, 3, 4]
    ]
    
    def create_matrix_grid(data, highlight_region=None, cell_size=35):
        """Create a visual matrix with optional highlighting."""
        rows = len(data)
        cols = len(data[0]) if data else 0
        
        with GridLayout(cols=cols, gap=2) as grid:
            for r in range(rows):
                for c in range(cols):
                    value = data[r][c]
                    
                    # Check if this cell should be highlighted
                    is_highlighted = False
                    if highlight_region:
                        hr, hc, hw, hh = highlight_region  # row, col, width, height
                        if hr <= r < hr + hh and hc <= c < hc + hw:
                            is_highlighted = True
                    
                    # Style based on highlighting
                    fill_color = Colors.LightCyan if is_highlighted else Colors.White
                    stroke_color = Colors.Blue if is_highlighted else Colors.Gray
                    stroke_width = 2 if is_highlighted else 1
                    
                    # Create cell
                    cell = Rect(
                        w=cell_size, h=cell_size, 
                        fill=fill_color, 
                        stroke=stroke_color, 
                        width=stroke_width
                    )
                    
                    # Create a group with cell and text
                    with Group() as cell_group:
                        cell  # Add the cell to the group
                        text = Text(str(value), size=12, fill=Colors.Black, font="monospace")
                        text.move_to(Point(0, 0))  # Center relative to group
        
        return grid
    
    # Create the visualization using RowLayout
    with RowLayout(gap=60, align="middle") as operation:
        # Input matrix with highlight for current convolution window
        input_grid = create_matrix_grid(
            input_data,
            highlight_region=(0, 0, 3, 3)  # Top-left 3x3 region
        )
        
        # Convolution symbol
        conv_symbol = Text("⊛", size=30, fill=Colors.DarkBlue)
        
        # Kernel matrix (all highlighted as it's fully active)
        kernel_grid = create_matrix_grid(
            kernel_data,
            highlight_region=(0, 0, 3, 3)
        )
        
        # Equals symbol
        equals_symbol = Text("=", size=30, fill=Colors.DarkBlue)
        
        # Output matrix with current result highlighted
        output_grid = create_matrix_grid(
            output_data,
            highlight_region=(0, 0, 1, 1)  # Just the top-left result
        )
    
    canvas.add(operation)

    # Add matrix labels after row layout has finalized positions.
    labels = [
        ("Input (5x5)", input_grid),
        ("Kernel (3x3)", kernel_grid),
        ("Output (3x3)", output_grid),
    ]
    for label_text, grid in labels:
        label = Text(label_text, size=14, fill=Colors.Black, font="sans-serif")
        grid_bounds = grid.local()
        grid_pos = Point(grid.transform.tx, grid.transform.ty)
        label.move_to(Point(grid_pos.x, grid_pos.y - grid_bounds.height / 2 - 25))
        canvas.add(label)
    
    # Add title and explanation
    title = Text("Convolution Operation", size=20, fill=Colors.DarkBlue, font="serif")
    title.move_to(Point(450, 50))
    canvas.add(title)
    
    # Add step explanation
    explanation = Text("Highlighted regions show current computation step", 
                      size=12, fill=Colors.Gray, font="sans-serif")
    explanation.move_to(Point(450, 350))
    canvas.add(explanation)
    
    return canvas

def physics_bounce_demo():
    """Creates a simple physics simulation showing bouncing balls."""
    print("⚽ Creating physics simulation...")
    
    try:
        from tesserax.physics import World, Gravity, Material
        from tesserax.physics.colliders import CircleCollider, BoxCollider
        from tesserax.physics.core import Body
        from tesserax.animation import Scene
        
        canvas = Canvas(width=1200, height=800)
        world = World()
        
        # Create floor
        floor = Rect(w=600, h=20, fill=Colors.DarkGray, stroke=Colors.Black)
        floor.move_to(Point(300, 380))
        world.add(floor, static=True, material=Material(restitution=0.8))
        canvas.add(floor)
        
        # Create bouncing balls with different properties
        balls = []
        ball_data = [
            {"pos": (100, 50), "r": 15, "color": Colors.Red, "mass": 1.0},
            {"pos": (200, 100), "r": 20, "color": Colors.Blue, "mass": 1.5},
            {"pos": (300, 30), "r": 12, "color": Colors.Green, "mass": 0.8},
            {"pos": (400, 80), "r": 18, "color": Colors.Purple, "mass": 1.2},
            {"pos": (500, 40), "r": 16, "color": Colors.Orange, "mass": 1.1},
        ]
        
        for ball_info in ball_data:
            ball = Circle(
                r=ball_info["r"], 
                fill=ball_info["color"], 
                stroke=Colors.Black,
                width=1
            )
            ball.move_to(Point(*ball_info["pos"]))
            
            world.add(
                ball,
                mass=ball_info["mass"],
                material=Material(restitution=0.7, friction=0.3),
                collider=CircleCollider(ball_info["r"])
            )
            canvas.add(ball)
        
        # Add gravity
        world.fields.append(Gravity())
        
        # Create side walls for containment
        left_wall = Rect(w=20, h=400, fill=Colors.DarkGray, stroke=Colors.Black)
        left_wall.move_to(Point(10, 200))
        world.add(left_wall, static=True, material=Material(restitution=0.8))
        canvas.add(left_wall)
        
        right_wall = Rect(w=20, h=400, fill=Colors.DarkGray, stroke=Colors.Black)
        right_wall.move_to(Point(590, 200))
        world.add(right_wall, static=True, material=Material(restitution=0.8))
        canvas.add(right_wall)
        
        # For now, just return the static canvas since physics simulation 
        # requires animation system which is complex to demonstrate here
        title = Text("Physics Simulation Setup", size=16, fill=Colors.DarkBlue)
        title.move_to(Point(300, 30))
        canvas.add(title)
        
        return canvas
        
    except ImportError:
        # Fallback if physics module isn't fully available
        canvas = Canvas(width=1200, height=800)
        message = Text("Physics simulation requires full Tesserax physics module", 
                      size=14, fill=Colors.Red)
        message.move_to(Point(300, 200))
        canvas.add(message)
        return canvas

def main():
    """Run all advanced examples and save them as SVG files."""
    print("🚀 Creating advanced Tesserax examples...\n")
    
    examples = [
        ("force_network", force_directed_network),
        ("hierarchical_tree", hierarchical_tree_layout),
        ("neural_network", neural_network_visualization),
        ("convolution_demo", convolutional_operation_demo),
        ("physics_bounce", physics_bounce_demo),
    ]
    
    batch: list[tuple[Canvas, RenderConfig]] = []
    successful_names: list[str] = []

    for name, func in examples:
        try:
            canvas = func()
            cfg = RenderConfig(
                output_path=f"{name}.svg",
                format="svg",
                viewport=ViewportSpec(fit_padding=24, fit_crop=False),
            )
            batch.append((canvas, cfg))
            successful_names.append(name)
        except Exception as e:
            print(f"   ❌ Error creating {name}: {e}")

    try:
        results = render_batch(batch)
        for name, result in zip(successful_names, results):
            print(f"   ✅ Saved: {name} -> {result.output_path}")
    except Exception as e:
        print(f"   ❌ Error rendering batch outputs: {e}")
    
    print("🎉 Advanced examples completed!")
    print("=== ADVANCED TESSERAX FEATURES DEMONSTRATED ===")
    print("🌐 Force-Directed Layout: Automatic graph positioning using physics")
    print("🌳 Hierarchical Layout: Tree structures with automatic ranking")
    print("🧠 Neural Networks: Complex multi-layer visualizations") 
    print("🔄 Matrix Operations: Detailed mathematical operation displays")
    print("⚽ Physics Simulation: Gravity, collisions, and material properties")
    print("📚 Key Advanced Concepts:")
    print("• ForceLayout: Fruchterman-Reingold algorithm for graph layouts")
    print("• HierarchicalLayout: DAG visualization with topological sorting")
    print("• GridLayout: Matrix-style arrangements with precise alignment")
    print("• Physics World: Deterministic simulation with baked animations")
    print("• Complex compositions: Nested layouts and procedural generation")

if __name__ == "__main__":
    main()
