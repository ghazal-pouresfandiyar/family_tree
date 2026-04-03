import os
import re
import subprocess
from hashlib import md5


class ImageManager:
    def __init__(self, image_folder="img", fallback_image="prof.jpeg", image_node_width=10, image_node_height=10):
        self.image_folder = image_folder
        self.fallback_image = fallback_image
        self.image_node_width = image_node_width
        self.image_node_height = image_node_height
        self._image_size_cache = {}

    def choose_image(self, person):
        candidates = []
        if person.person_id != 1:
            candidates.extend(
                [
                    f"{person.name} {person.person_id}",
                    f"{person.name}_{person.person_id}",
                    f"{person.name} ({person.person_id})",
                ]
            )
        else:
            candidates.append(person.name)

        for ext in [".jpeg", ".jpg", ".png"]:
            for base_name in candidates:
                full_path = os.path.join(self.image_folder, f"{base_name}{ext}")
                if os.path.exists(full_path):
                    return full_path

        if person.gender in ["female", "male"]:
            gender_image = os.path.join(self.image_folder, f"{person.gender}.jpeg")
            if os.path.exists(gender_image):
                return gender_image

        fallback_path = os.path.join(self.image_folder, self.fallback_image)
        if os.path.exists(fallback_path):
            return fallback_path

        return None

    def image_pixel_size(self, image_path):
        if image_path in self._image_size_cache:
            return self._image_size_cache[image_path]

        width = height = None
        try:
            result = subprocess.run(
                ["sips", "-g", "pixelWidth", "-g", "pixelHeight", image_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                match_width = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
                match_height = re.search(r"pixelHeight:\s*(\d+)", result.stdout)
                if match_width and match_height:
                    width = int(match_width.group(1))
                    height = int(match_height.group(1))
        except Exception:
            pass

        self._image_size_cache[image_path] = (width, height)
        return width, height

    def image_render_size(self, image_path):
        # Graphviz width/height are in inches; keep node sizes realistic.
        base_width = self.image_node_width * 0.05
        base_height = self.image_node_height * 0.05

        filename = os.path.basename(image_path).lower()
        if filename.startswith("female") or filename.startswith("male"):
            return str(base_width), str(base_height)

        pixel_width, pixel_height = self.image_pixel_size(image_path)
        if pixel_width and pixel_height:
            ratio = abs(pixel_width - pixel_height) / max(pixel_width, pixel_height)
            if ratio <= 0.10:
                return str(round(base_width, 2)), str(round(base_height, 2))

        return str(base_width), str(base_height)

    def rounded_image_path(self, image_path, border_color, border_px):
        if not image_path or not os.path.exists(image_path):
            return image_path

        try:
            from PIL import Image, ImageDraw
        except Exception:
            return image_path

        cache_dir = os.path.join(self.image_folder, ".rounded_cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_key = md5(f"{image_path}|{os.path.getmtime(image_path)}".encode("utf-8")).hexdigest()
        rounded_path = os.path.join(cache_dir, f"{cache_key}.png")
        if os.path.exists(rounded_path):
            return rounded_path

        try:
            with Image.open(image_path).convert("RGBA") as img:
                width, height = img.size
                radius = max(12, min(width, height) // 6)

                mask = Image.new("L", (width, height), 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)

                rounded = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                rounded.paste(img, (0, 0), mask)
                rounded.save(rounded_path, format="PNG")
                return rounded_path
        except Exception:
            return image_path
