# Image Steganography

A Python script to hide files inside images using LSB (Least Significant Bit) steganography. It supports embedding any file type (text, PDF, images) into a cover image and includes tools for visual and file size analysis.

## Requirements

Install the necessary dependencies before running the script:

```bash
pip install opencv-python numpy matplotlib
```

## Usage

The script uses a simple command-line interface with three main commands: `hide`, `reveal`, and `analyze`.

### Hiding a File

Use the `hide` command to embed a secret file into a cover image. 

```bash
python stego.py hide cover.png secret.pdf -o stego_image.png
```
*Note: Always save the output image as a `.png`. Saving it as a compressed format like `.jpg` will destroy the hidden data.*

### Revealing a File

Use the `reveal` command to extract the hidden file. The script automatically reads the original filename and size from the image metadata.

```bash
python stego.py reveal stego_image.png
```
*The extracted file will be saved in an `output/` directory by default.*

### Analyzing Images

Use the `analyze` command to compare the original cover image with the generated stego image.

```bash
python stego.py analyze cover.png stego_image.png
```
*This command outputs the file size differences and generates a side-by-side histogram (`histogram_comparison.png`) to verify that the visual quality remains identical.*
