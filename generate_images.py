from PIL import Image, ImageDraw, ImageFont
import os

def generate_image_from_text(text_line, font_path, background_image_path, output_folder, image_index):
    """
    Generates an image from a single line of text, placing it on a background image.

    Args:
        text_line (str): The text to be rendered.
        font_path (str): Path to the .ttf font file.
        background_image_path (str): Path to the background image file.
        output_folder (str): Folder to save the generated images.
        image_index (int): Index to name the output image file.
    """
    try:
        # Open the background image
        background = Image.open(background_image_path).convert("RGBA")
        width, height = background.size

        # Load the font (adjust font size as needed)
        # You might need to experiment with font_size for optimal fit
        font_size = 150 # Starting font size, will be adjusted
        font = ImageFont.truetype(font_path, font_size)

        # Create a drawing object
        draw = ImageDraw.Draw(background)

        # Get text bounding box to calculate its size
        # Use textbbox for more accurate bounding box
        bbox = draw.textbbox((0, 0), text_line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Adjust font size if text is too wide for the image
        while text_width > width * 0.9 and font_size > 10: # Keep some margin, min font size 10
            font_size -= 5
            font = ImageFont.truetype(font_path, font_size)
            bbox = draw.textbbox((0, 0), text_line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

        # Calculate text position to center it
        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # Define text color (RGBA - Red, Green, Blue, Alpha)
        # Black color with full opacity
        text_color = (0, 0, 0, 255)

        # Draw the text on the background
        draw.text((x, y), text_line, font=font, fill=text_color)

        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Save the generated image
        output_filename = os.path.join(output_folder, f"output_image_{image_index}.png")
        background.save(output_filename)
        print(f"Generated: {output_filename} for text: '{text_line.strip()}'")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# --- Configuration ---
TEXT_FILE = "thai.txt"
FONT_PATH = "Sarun's ThangLuang.ttf" # Make sure this file is in the same directory as your script
BACKGROUND_IMAGE_PATH = "BG/bg_1.jpg" # Make sure this path is correct
OUTPUT_FOLDER = "generated_images"

# --- Main execution ---
if __name__ == "__main__":
    if not os.path.exists(TEXT_FILE):
        print(f"Error: The text file '{TEXT_FILE}' was not found.")
    elif not os.path.exists(FONT_PATH):
        print(f"Error: The font file '{FONT_PATH}' was not found.")
    elif not os.path.exists(BACKGROUND_IMAGE_PATH):
        print(f"Error: The background image '{BACKGROUND_IMAGE_PATH}' was not found. Please check the 'BG' folder and file name.")
    else:
        with open(TEXT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Strip whitespace and check if the line is not empty
            clean_line = line.strip()
            if clean_line:
                generate_image_from_text(clean_line, FONT_PATH, BACKGROUND_IMAGE_PATH, OUTPUT_FOLDER, i + 1)