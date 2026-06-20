# Family Tree

A beautiful, interactive family tree visualization with scrollable branches, color-coded connections, and photo support.

## Quick Start

1. Edit `tree.txt` with your family data
2. Add photos to `img/` folder
3. Run `python3 generate.py`
4. Open `index.html` in a browser

## tree.txt Format

Each line represents a marriage and its children:

```
Parent1 & Parent2 : Child1, Child2, Child3
```

### Rules

- **Line 1** (Root): The root couple and their children
  ```
  Grandpa & Grandma : Child1, Child2
  ```

- **Subsequent lines**: Each child's marriage and children
  ```
  Child1 & Spouse1 : Grandchild1, Grandchild2
  Child2 & Spouse2 : Grandchild3
  ```

- **No children**: Use `0`
  ```
  Person1 & Person2 : 0
  ```

- **Gender markers** (optional): Add `m` or `f` after child names
  ```
  Parent1 & Parent2 : Child1 m, Child2 f
  ```

- **Duplicate names**: Add an ID number to distinguish people with the same name
  ```
  Parent1 & Parent2 : Mojtaba m, Fati f
  Fati & Mojtaba 2 : 0
  ```
  Here, Mojtaba (no ID) and Mojtaba 2 are different people.

### Example

```
Roghaye & Yousef : Agha_Hajbaba m, Madarbozorg f
Khanoum_joon & Agha_Hajbaba : Ame_Parvin f, Fattah m
Madarbozorg & Aghabozorg : Khale_Maryam f, Khale_Mina f
Ame_Parvin & Amo_Khosro : Soulmaz f, Sorour f
Soulmaz & Mehdi 2 : Mehrad m, Mehrbod m
```

## Photo Guidelines

### File Naming

Photos must be named exactly as the person appears in `tree.txt`:

| Name in tree.txt | Photo filename |
|------------------|----------------|
| `Agha_Hajbaba` | `Agha_Hajbaba.jpeg` |
| `Mojtaba 2` | `Mojtaba 2.jpeg` |
| `Ali` | `Ali.jpeg` |
| `Ali 2` | `Ali 2.jpeg` |

### Requirements

- **Format**: JPEG (`.jpeg`) recommended
- **Shape**: Square images work best (they'll be cropped to circles)
- **Size**: 200x200px or larger
- **Location**: Place in `img/` folder

### Fallback

If a photo is missing, the tree shows the person's initial with a colored border.

## Commands

```bash
# Generate HTML from tree.txt
python3 generate.py

# Open in browser (Mac)
open index.html

# Open in browser (Windows)
start index.html
```

## Project Structure

```
family_tree/
├── generate.py      # Script to generate HTML
├── tree.txt         # Family data
├── index.html       # Generated HTML (output)
├── img/             # Photos folder
│   ├── Person1.jpeg
│   ├── Person2.jpeg
│   └── ...
└── README.md        # This file
```

## Customization

### Colors

Edit the `COLORS` list in `generate.py` to change the branch colors:

```python
COLORS = [
    "#c07b8a",  # Pink
    "#7ba5c4",  # Blue
    "#8bc47b",  # Green
    # Add more colors...
]
```

### Theme

Change the background color and accents in the CSS section of `generate.py`:

```css
background: #fdf8ed;  /* Background color */
border: 3px solid #c3a578;  /* Accent color */
```

## Features

- Scrollable horizontal layout for large families
- Color-coded branches for each sibling
- Shade-based colors for children (same family = same color family)
- Cross-branch marriage connections
- Mobile responsive
- Save as PDF button
- Photo fallback with initials
