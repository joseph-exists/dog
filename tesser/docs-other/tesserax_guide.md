# Tesserax SVG Library - Quick Reference Guide

<cite index="1-5,1-22,1-49,1-50,11-2,11-17,12-2,12-3">Tesserax is a Python library that "speaks fluent SVG" and allows you to create vector graphics programmatically. It's designed to work seamlessly in Jupyter notebooks and uses Python's native syntax without requiring a domain-specific language.</cite>

## Core Concepts

### 1. Canvas - Your Drawing Surface
```python
from tesserax import Canvas
canvas = Canvas(width=400, height=300)
```
The Canvas is where all your shapes live. You specify dimensions and then add shapes to it.

### 2. Basic Shapes

#### Circle
```python
from tesserax import Circle, Colors
circle = Circle(r=50, fill=Colors.LightBlue, stroke=Colors.Blue, width=2)
```
- `r`: radius
- `fill`: interior color
- `stroke`: border color  
- `width`: border thickness

#### Rectangle
```python
from tesserax import Rect
rect = Rect(w=100, h=60, fill=Colors.LightGreen, stroke=Colors.Green)
```
- `w`: width
- `h`: height

#### Text
```python
from tesserax import Text
text = Text("Hello SVG!", size=16, fill=Colors.DarkRed, font="sans-serif")
```
- `size`: font size
- `font`: font family (e.g., "serif", "monospace")
- `anchor`: text alignment ("start", "middle", "end")
- `baseline`: vertical alignment ("top", "middle", "bottom")

#### Arrow
```python
from tesserax import Arrow, Point
arrow = Arrow(
    p1=Point(10, 10),    # start point
    p2=Point(100, 10),   # end point
    stroke=Colors.Black,
    width=2
)
```

### 3. Positioning with Points
```python
from tesserax import Point

# Create a point
pos = Point(100, 50)

# Position a shape
shape.move_to(Point(x, y))
```

### 4. Colors
```python
from tesserax import Colors

# Use predefined colors
Colors.Red
Colors.Blue
Colors.LightGreen
Colors.DarkBlue
Colors.Transparent

# Or create custom colors
from tesserax import Color
custom_color = Color(255, 128, 0)  # RGB values
```

### 5. Assembly - Building Your Drawing
```python
# Add shapes to canvas
canvas.add(circle)
canvas.add(rect)
canvas.add(text)
canvas.add(arrow)
```

### 6. Export to SVG
```python
# Save to file
canvas.save("my_drawing.svg")

# Get as string
svg_string = str(canvas)
```

## Example Workflow

```python
from tesserax import Canvas, Circle, Rect, Text, Arrow, Point, Colors

# 1. Create canvas
canvas = Canvas(width=300, height=200)

# 2. Create shapes
circle = Circle(r=30, fill=Colors.Tomato)
rect = Rect(w=60, h=40, fill=Colors.LightBlue)
label = Text("My Drawing", size=14, fill=Colors.Black)

# 3. Position shapes
circle.move_to(Point(80, 100))
rect.move_to(Point(200, 100))
label.move_to(Point(150, 30))

# 4. Connect with arrow
arrow = Arrow(
    p1=Point(110, 100),  # right edge of circle
    p2=Point(170, 100),  # left edge of rect
    stroke=Colors.Gray
)

# 5. Assemble
canvas.add(circle)
canvas.add(rect)
canvas.add(label)
canvas.add(arrow)

# 6. Export
canvas.save("example.svg")
```

## Key Advantages of Tesserax

<cite index="1-12,1-38,1-39,11-17,11-18,11-19,11-20">1. **Native SVG Output**: Bypasses fragile conversion layers and targets SVG directly
2. **Semantic Scaling**: Works perfectly with responsive web design
3. **CSS Styling**: SVG output can be styled with CSS
4. **Browser Optimized**: Uses the modern web browser as the rendering engine</cite>

<cite index="1-24,1-25,11-24,11-25,11-26">2. **Zero Dependencies**: Pure Python with no external requirements
3. **Fully Typed**: Complete type hints for better IDE support</cite>

<cite index="1-13,11-12,11-13">3. **Python Native**: No new syntax to learn - just Python
4. **IDE Support**: Full debugging, linting, and autocomplete support</cite>

<cite index="1-53,1-26,1-27,1-28,11-1,11-2,11-3">4. **Smart Positioning**: Advanced anchor system means no manual coordinates or magic numbers
5. **Relational Geometry**: Objects know where they are relative to each other</cite>

## When to Use Tesserax

- **Scientific Illustrations**: <cite index="1-49,1-53,12-2,12-15,12-28,12-29">Perfect for creating diagrams in research papers and educational content</cite>
- **Technical Diagrams**: Algorithm visualizations, data structures, flowcharts
- **Jupyter Notebooks**: <cite index="1-22,1-49">Designed to work seamlessly in notebook environments</cite>
- **Web Graphics**: <cite index="1-37,1-38">SVG output is perfect for responsive web design</cite>

<cite index="1-41,1-53">Use Tesserax for concepts and diagrams, while using matplotlib/Altair for data visualization.</cite>