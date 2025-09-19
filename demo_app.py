"""Demo FastHTML application for the JSON Schema to UI library."""

import json
import sys
import argparse
from pathlib import Path
import webbrowser
from fasthtml.common import *
from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
from cjm_fasthtml_daisyui.core.testing import create_theme_selector
from cjm_fasthtml_daisyui.components.navigation.navbar import navbar, navbar_start, navbar_center, navbar_end
from cjm_fasthtml_daisyui.components.actions.button import btn, btn_colors, btn_styles
from cjm_fasthtml_daisyui.utilities.semantic_colors import bg_dui, text_dui
from cjm_fasthtml_tailwind.utilities.effects import shadow
from cjm_fasthtml_tailwind.utilities.flexbox_and_grid import flex_display, gap, grid_cols, items, justify, grid_display, flex
from cjm_fasthtml_tailwind.utilities.spacing import p, m
from cjm_fasthtml_tailwind.utilities.sizing import container, max_w
from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight
from cjm_fasthtml_tailwind.core.base import combine_classes

# Import our library
from cjm_fasthtml_jsonschema.generators.form import generate_form_ui

static_path = Path(__file__).absolute().parent

# Create the FastHTML app with DaisyUI headers
app, rt = fast_app(
    pico=False,
    hdrs=[*get_daisyui_headers()],
    title="JSON Schema to UI Demo",
    static_path=str(static_path)
)

app.hdrs.append(Link(rel='icon', type='image/png', href='/static/layout-template.png'))  # for PNG


# Global variable to store schema path
SCHEMA_PATH = None

def load_test_schema():
    """Load the test JSON schema file."""
    schema_path = Path(SCHEMA_PATH)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return json.load(f)


def get_default_values_from_schema(schema):
    """Extract default values from a JSON schema."""
    values = {}
    properties = schema.get("properties", {})

    for prop_name, prop_schema in properties.items():
        if "default" in prop_schema:
            values[prop_name] = prop_schema["default"]

    return values


@rt("/")
def index():
    """Main page showing the generated form."""
    # Load the schema
    schema = load_test_schema()

    # Get default values from the schema itself
    example_values = get_default_values_from_schema(schema)

    # Generate the form UI
    form_ui = generate_form_ui(
        schema=schema,
        values=example_values,
        show_title=True,
        show_description=True,
        compact=True,
        card_wrapper=True
    )

    return Div(
        # Navbar with improved styling and mobile responsiveness
        Div(
            Div(
                Div(
                    H1("JSON Schema to FastHTML UI Demo",
                    cls=combine_classes(
                        font_size.lg,          # Smaller on mobile
                        font_size.xl.sm,       # Medium on small screens
                        font_size._2xl.md,     # Large on medium+ screens
                        font_weight.bold,
                        text_dui.base_content
                    )),
                    cls=str(navbar_start)
                ),
                Div(
                    create_theme_selector(),
                    cls=combine_classes(
                        flex_display,
                        justify.end,
                        items.center,
                        gap(2),               # Smaller gap on mobile
                        gap(4).sm,            # Normal gap on small+
                        navbar_end
                    )
                ),
                cls=combine_classes(
                    navbar,
                    bg_dui.base_100,
                    p(0)
                )
            ),
            P(
                "This demo shows a configuration form generated from a JSON Schema",
                cls=combine_classes(
                    font_size.lg,
                    m.b(8)
                )
            ),
        ),
        

        # Generated form
        Form(
            form_ui,

            # Add submit button
            Div(
                Button(
                    "Save Configuration",
                    type="submit",
                    cls=combine_classes(btn, btn_colors.primary)
                ),
                Button(
                    "Reset",
                    type="reset",
                    cls=combine_classes(btn, btn_styles.ghost, m.l(2))
                ),
                cls=combine_classes(m.t(6))
            ),

            # Form submission handler
            hx_post="/submit",
            hx_target="#result",
            hx_swap="innerHTML"
        ),

        # Result display area
        Div(id="result", cls=combine_classes(m.t(6))),

        cls=combine_classes(
            container,
            max_w._6xl,
            m.x.auto,
            p(6)
        )
    )


@rt("/submit", methods=["POST"])
async def submit(request):
    """Handle form submission."""
    form_data = await request.form()

    # Convert form data to dict
    config = dict(form_data)

    # Handle boolean fields (checkboxes)
    schema = load_test_schema()
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if prop_schema.get("type") == "boolean":
            # Checkbox fields only appear in form data if checked
            config[prop_name] = prop_name in config

    # Convert numeric fields
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if prop_name in config:
            if prop_schema.get("type") == "integer":
                try:
                    config[prop_name] = int(config[prop_name])
                except (ValueError, TypeError):
                    pass
            elif prop_schema.get("type") == "number":
                try:
                    config[prop_name] = float(config[prop_name])
                except (ValueError, TypeError):
                    pass

    # Return formatted result
    return Div(
        H3("Submitted Configuration:", cls=combine_classes(font_weight.bold, m.b(2))),
        Pre(
            json.dumps(config, indent=2),
            cls=combine_classes(
                bg_dui.base_100,
                p(4),
                "rounded-lg",
                "overflow-auto"
            )
        ),
        cls=combine_classes(
            bg_dui.success.opacity(10),
            "border",
            "border-success",
            p(4),
            "rounded-lg"
        )
    )


def open_browser(url):
    # Open in default browser
    print(f"Opening in browser at {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    import threading

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="JSON Schema to UI Demo Application")
    parser.add_argument(
        "--schema",
        type=str,
        default="test_files/voxtral_config_schema.json",
        help="Path to the JSON schema file (default: test_files/voxtral_config_schema.json)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port to run the server on (default: 5001)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    # Set the global schema path
    SCHEMA_PATH = args.schema

    # Verify schema file exists
    if not Path(SCHEMA_PATH).exists():
        print(f"Error: Schema file not found: {SCHEMA_PATH}")
        print("\nAvailable schema files:")
        for schema_file in Path("test_files").glob("*_schema.json"):
            print(f"  - {schema_file}")
        sys.exit(1)

    # Load and display schema info
    try:
        with open(SCHEMA_PATH, "r") as f:
            schema_data = json.load(f)
            schema_title = schema_data.get("title", "Unknown")
            schema_desc = schema_data.get("description", "No description")
    except Exception as e:
        print(f"Error loading schema: {e}")
        sys.exit(1)

    # Run the app
    import uvicorn
    print("\n" + "="*60)
    print("JSON Schema to UI Demo App")
    print("="*60)
    print(f"\nSchema: {SCHEMA_PATH}")
    print(f"Title: {schema_title}")
    print(f"Description: {schema_desc}")
    print(f"\nServer: http://{args.host}:{args.port}")
    print("\nAvailable routes:")
    print(f"  http://localhost:{args.port}/          - Main demo with pre-filled form")
    print(f"  http://localhost:{args.port}/empty     - Empty form without values")
    print(f"  http://localhost:{args.port}/compact   - Compact form layout")
    print("\n" + "="*60 + "\n")

    # Open browser after a short delay
    timer = threading.Timer(1.5, lambda: open_browser(f"http://localhost:{args.port}"))
    timer.daemon = True
    timer.start()

    uvicorn.run(app, host=args.host, port=args.port)