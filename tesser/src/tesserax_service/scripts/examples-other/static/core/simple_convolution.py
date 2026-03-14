#!/usr/bin/env python3
"""Simple convolution operation demonstration."""

from tesserax import Canvas, Rect, Text, Point, Colors, RenderConfig, render_scene

def create_simple_matrix(data, name, highlight=None, cell_size=35):
    """Create a simple matrix without complex grouping."""
    rows = len(data)
    cols = len(data[0]) if data else 0
    gap = 2
    margin = 20
    title_gap = 28
    matrix_w = cols * cell_size + (cols - 1) * gap
    matrix_h = rows * cell_size + (rows - 1) * gap

    canvas = Canvas(
        width=matrix_w + margin * 2,
        height=matrix_h + margin * 2 + title_gap,
    )
    
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            # Determine if highlighted
            is_highlighted = (highlight and 
                            highlight[0] <= r < highlight[0] + highlight[2] and 
                            highlight[1] <= c < highlight[1] + highlight[3])
            
            # Create cell
            cell = Rect(
                w=cell_size, h=cell_size,
                fill=Colors.LightCyan if is_highlighted else Colors.White,
                stroke=Colors.Blue if is_highlighted else Colors.Gray,
                width=2 if is_highlighted else 1
            )
            
            # Position cell
            x = margin + cell_size / 2 + c * (cell_size + gap)
            y = margin + title_gap + cell_size / 2 + r * (cell_size + gap)
            cell.move_to(Point(x, y))
            canvas.add(cell)
            
            # Add text
            text = Text(str(value), size=12, fill=Colors.Black, font="monospace")
            text.move_to(Point(x, y))
            canvas.add(text)
    
    # Add title
    title = Text(name, size=14, fill=Colors.Black)
    title.move_to(Point(margin + matrix_w / 2, margin))
    canvas.add(title)

    # Ensure exported SVG viewBox tightly encloses all drawn content.
    canvas.fit(padding=8, crop=True)
    
    return canvas

def main():
    # Just create a simple version
    input_data = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
    
    canvas = create_simple_matrix(input_data, "Simple Matrix", highlight=(0, 0, 2, 2))
    result = render_scene(
        canvas,
        RenderConfig(
            output_path="convolution_demo.svg",
            format="svg",
        ),
    )
    print(f"✅ Saved: {result.output_path}")

if __name__ == "__main__":
    main()
