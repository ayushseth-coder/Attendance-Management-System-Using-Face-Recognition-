import cv2
import numpy as np

def analyze_image(img_path):
    print(f"\n--- Analyzing {img_path} ---")
    img = cv2.imread(img_path)
    if img is None:
        print("Image not found!")
        return

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur / Sharpness (Laplacian Variance)
    # Screens/Prints often have lower variance if blurry, or higher if Moire is present
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(f"Laplacian Variance (Sharpness): {laplacian_var:.2f}")
    
    # 2. Specular Reflection / Glare (Blown out pixels)
    # Count pixels that are almost pure white (intensity > 240)
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    glare_ratio = cv2.countNonZero(mask) / (gray.shape[0] * gray.shape[1])
    print(f"Glare Ratio (Intensity > 240): {glare_ratio:.5f}")
    
    # 3. HSV Color Variance
    # Skin has specific hue/sat ranges. Screens might have lower saturation variance.
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    print(f"Saturation Mean: {s.mean():.2f}, Saturation Var: {s.var():.2f}")
    print(f"Value Mean: {v.mean():.2f}, Value Var: {v.var():.2f}")

    # 4. Local Binary Pattern (LBP) approximation / Edge Density
    edges = cv2.Canny(gray, 100, 200)
    edge_density = cv2.countNonZero(edges) / (gray.shape[0] * gray.shape[1])
    print(f"Edge Density: {edge_density:.5f}")

analyze_image("real_face.jpg")
analyze_image("fake_print.jpg")
