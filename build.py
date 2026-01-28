import os
import subprocess
import sys


def build_app():
    # Проверяем существование иконки
    icon_path = "images/main_icon.ico"
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file {icon_path} not found!")
        print("Creating ICO file from PNG...")

        try:
            from PIL import Image

            png_path = "images/main_icon.png"
            if os.path.exists(png_path):
                img = Image.open(png_path)
                img.save(
                    icon_path,
                    format="ICO",
                    sizes=[
                        (256, 256),
                        (128, 128),
                        (64, 64),
                        (48, 48),
                        (32, 32),
                        (16, 16),
                    ],
                )
                print(f"Created {icon_path} from PNG")
            else:
                print(f"Error: PNG file {png_path} also not found!")
                return
        except ImportError:
            print("Error: Pillow not installed. Install with: pip install Pillow")
            return

    # Команда сборки
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        "--add-data",
        "images:images",
        "--name",
        "WorkTimeTracker",  # Имя выходного файла
        "main.py",
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\nBuild successful!")
        print(f"Executable: dist/WorkTimeTracker.exe")
    else:
        print("\nBuild failed!")


if __name__ == "__main__":
    build_app()
