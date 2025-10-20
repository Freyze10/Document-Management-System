
from utils import abs_path

from reportlab.lib import colors
from reportlab.lib.units import cm


def add_first_page_header(canvas, doc):
    canvas.saveState()
    # Convert cm to points (1 cm ≈ 28.35 pt)
    logo_width = 17.29 * cm
    logo_height = 3.32 * cm
    # Page size
    page_width, page_height = doc.pagesize

    logo_path = abs_path.resource("img/MBPI_Logo.jpg")

    # Center horizontally
    x = (page_width - logo_width) / 2
    y = page_height - logo_height  # topmost position

    # Draw logo with fixed size (ignore aspect ratio)
    canvas.drawImage(
        logo_path,
        x, y,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=False
    )


def add_coa_header(canvas, doc, header_only=False):
    from reportlab.lib.units import cm

    canvas.saveState()

    # Page size and margins
    page_width, page_height = doc.pagesize
    left_margin = doc.leftMargin
    right_margin = doc.rightMargin

    # --- First Logo: stretched edge to edge ---
    logo_path = abs_path.resource("img/MBPI_Logo.jpg")
    logo_width = page_width - left_margin - right_margin
    logo_height = 3.32 * cm
    x_logo = left_margin
    y_logo_top = page_height - logo_height
    canvas.drawImage(
        logo_path,
        x_logo, y_logo_top,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=False
    )

    # --- COA Title: fixed size and centered ---
    second_image_path = abs_path.resource("img/coa_title.png")
    second_image_width = 11.16 * cm
    second_image_height = 1.45 * cm

    # Center horizontally
    x_second_image = (page_width - second_image_width) / 2
    # Place immediately below logo, with slight overlap or gap as desired
    y_second_image_top = y_logo_top - second_image_height - (0.2 * cm)  # Adjust overlap/gap here

    try:
        canvas.drawImage(
            second_image_path,
            x_second_image, y_second_image_top,
            width=second_image_width,
            height=second_image_height,
            preserveAspectRatio=True  # Should keep it proportional, but size is always constrained
        )
    except Exception as e:
        print(f"Warning: Could not draw second image at {second_image_path}. Error: {e}")

    canvas.setFont('Times-Roman', 9)
    canvas.setFillColorRGB(0.1, 0.1, 0.1)

    form_id_text = "FM00003A"
    text_width = canvas.stringWidth(form_id_text, 'Times-Roman', 9)
    canvas.drawString(
        page_width - right_margin - text_width,
        doc.bottomMargin + 15,
        form_id_text
    )

    canvas.restoreState()


def add_coa_header_only(canvas, doc, header_only=False):
    from reportlab.lib.units import cm

    canvas.saveState()

    # Page size and margins
    page_width, page_height = doc.pagesize
    left_margin = doc.leftMargin
    right_margin = doc.rightMargin

    # --- First Logo: stretched edge to edge ---
    logo_path = abs_path.resource("img/MBPI_Logo.jpg")
    logo_width = page_width - left_margin - right_margin
    logo_height = 3.32 * cm
    x_logo = left_margin
    y_logo_top = page_height - logo_height
    canvas.drawImage(
        logo_path,
        x_logo, y_logo_top,
        width=logo_width,
        height=logo_height,
        preserveAspectRatio=False
    )

    canvas.setFont('Times-Roman', 9)
    canvas.setFillColorRGB(0.1, 0.1, 0.1)

    form_id_text = "FM00003A"
    text_width = canvas.stringWidth(form_id_text, 'Times-Roman', 9)
    canvas.drawString(
        page_width - right_margin - text_width,
        doc.bottomMargin + 15,
        form_id_text
    )

    canvas.restoreState()
