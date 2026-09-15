import os
import struct
import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse

def bytes_to_bits(data):
    # Convert bytes to a 1D numpy array of bits
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

def bits_to_bytes(bits):
    # Pack bits back into bytes
    return np.packbits(bits).tobytes()

def hide_file(cover_path, secret_path, output_path):
    print(f"Hiding '{secret_path}' into '{cover_path}'...")
    
    img = cv2.imread(cover_path)
    if img is None:
        raise ValueError(f"Could not open cover image: {cover_path}")
        
    with open(secret_path, 'rb') as f:
        secret_data = f.read()
        
    secret_filename = os.path.basename(secret_path).encode('utf-8')
    
    # Structure: [4 bytes filename len] + [filename] + [4 bytes data len] + [data]
    header = struct.pack('>I', len(secret_filename)) + secret_filename + struct.pack('>I', len(secret_data))
    payload = header + secret_data
    
    payload_bits = bytes_to_bits(payload)
    
    # Check if image has enough capacity (1 bit per color channel)
    max_bits = img.shape[0] * img.shape[1] * img.shape[2]
    if len(payload_bits) > max_bits:
        raise ValueError(f"Secret file is too large. Need {len(payload_bits)} bits, max capacity is {max_bits} bits.")
        
    print(f"Embedding {len(payload_bits)} bits into the image (capacity: {max_bits} bits)...")
    
    flat_img = img.flatten()
    
    # Clear the LSB of the pixels we are going to modify and inject our bits
    flat_img[:len(payload_bits)] = (flat_img[:len(payload_bits)] & 254) | payload_bits
    
    stego_img = flat_img.reshape(img.shape)
    
    # Save as PNG to avoid compression artifacts breaking the payload
    cv2.imwrite(output_path, stego_img)
    print(f"Stego image saved to '{output_path}'")

def reveal_file(stego_path, output_dir):
    print(f"Revealing secret from '{stego_path}'...")
    
    img = cv2.imread(stego_path)
    if img is None:
        raise ValueError(f"Could not open stego image: {stego_path}")
        
    flat_img = img.flatten()
    
    # Extract LSBs from all pixels
    all_bits = flat_img & 1
    
    if len(all_bits) < 32:
        raise ValueError("Image doesn't contain valid hidden data.")
        
    # Read filename length
    filename_len_bits = all_bits[:32]
    filename_len_bytes = bits_to_bytes(filename_len_bits)
    filename_len = struct.unpack('>I', filename_len_bytes)[0]
    
    idx = 32
    if len(all_bits) < idx + filename_len * 8:
        raise ValueError("Image doesn't contain valid hidden data.")
        
    # Read filename
    filename_bits = all_bits[idx:idx + filename_len * 8]
    filename = bits_to_bytes(filename_bits).decode('utf-8')
    
    idx += filename_len * 8
    
    if len(all_bits) < idx + 32:
        raise ValueError("Image doesn't contain valid hidden data.")
        
    # Read data length
    file_len_bits = all_bits[idx:idx + 32]
    file_len_bytes = bits_to_bytes(file_len_bits)
    file_len = struct.unpack('>I', file_len_bytes)[0]
    
    idx += 32
    
    if len(all_bits) < idx + file_len * 8:
        raise ValueError("Image doesn't contain valid hidden data.")
        
    # Read data payload
    file_bits = all_bits[idx:idx + file_len * 8]
    file_data = bits_to_bytes(file_bits)
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'wb') as f:
        f.write(file_data)
        
    print(f"Secret file revealed and saved to '{output_path}'")

def analyze(cover_path, stego_path, output_histogram="histogram_comparison.png"):
    print("\n--- Analysis ---")
    
    cover_size = os.path.getsize(cover_path)
    stego_size = os.path.getsize(stego_path)
    
    print(f"Cover Image Size: {cover_size} bytes")
    print(f"Stego Image Size: {stego_size} bytes")
    
    print("\nFile Size Check:")
    if cover_size == stego_size:
        print("The file sizes are identical. This is expected if both images share the exact same compression parameters.")
    else:
        print("The file sizes differ. This happens when the original cover image was compressed differently (e.g. JPG) than our generated PNG stego image, or uses different PNG optimization.")
        
    # Plot histograms to compare visual quality
    cover_img = cv2.imread(cover_path)
    stego_img = cv2.imread(stego_path)
    
    colors = ('b', 'g', 'r')
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.title("Cover Image Histogram")
    for i, color in enumerate(colors):
        hist = cv2.calcHist([cover_img], [i], None, [256], [0, 256])
        plt.plot(hist, color=color, alpha=0.7)
        plt.xlim([0, 256])
    plt.xlabel("Pixel Intensity")
    plt.ylabel("Frequency")
        
    plt.subplot(1, 2, 2)
    plt.title("Stego Image Histogram")
    for i, color in enumerate(colors):
        hist = cv2.calcHist([stego_img], [i], None, [256], [0, 256])
        plt.plot(hist, color=color, alpha=0.7)
        plt.xlim([0, 256])
    plt.xlabel("Pixel Intensity")
    plt.ylabel("Frequency")
        
    plt.tight_layout()
    plt.savefig(output_histogram)
    print(f"\nHistogram comparison saved to '{output_histogram}'")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Steganography CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    hide_parser = subparsers.add_parser("hide", help="Hide a file inside an image")
    hide_parser.add_argument("cover", help="Path to cover image")
    hide_parser.add_argument("secret", help="Path to the file to hide")
    hide_parser.add_argument("-o", "--output", default="stego.png", help="Output stego image path (default: stego.png)")
    
    reveal_parser = subparsers.add_parser("reveal", help="Reveal a hidden file from an image")
    reveal_parser.add_argument("stego", help="Path to stego image")
    reveal_parser.add_argument("-d", "--dir", default="output", help="Output directory (default: output/)")
    
    analyze_parser = subparsers.add_parser("analyze", help="Compare original and stego images")
    analyze_parser.add_argument("cover", help="Path to original cover image")
    analyze_parser.add_argument("stego", help="Path to stego image")
    
    args = parser.parse_args()
    
    if args.command == "hide":
        hide_file(args.cover, args.secret, args.output)
    elif args.command == "reveal":
        reveal_file(args.stego, args.dir)
    elif args.command == "analyze":
        analyze(args.cover, args.stego)
    else:
        parser.print_help()
