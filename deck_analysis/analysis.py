import os
import base64
import tempfile
import dotenv
from pathlib import Path
from pdf2image import convert_from_path
import io
from PIL import Image
import PIL
import asyncio
import aiohttp
import time

print(PIL.__version__)

from openai import OpenAI

dotenv.load_dotenv()

uploads_dir = Path("local_uploads")
descriptions_dir = Path("deck_descriptions")


def resize_image(image):
    # Resize the image to 512x512 pixels
    img = image.resize((512, 512), Image.LANCZOS)

    # Save the resized image to a BytesIO object
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


def save_pitchdeck_images(pitchdeck_file):
    pitch_deck_name = os.path.splitext(pitchdeck_file.name)[0]
    deck_dir = uploads_dir / pitch_deck_name
    deck_dir.mkdir(exist_ok=True)

    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pitchdeck_file.getvalue())
        temp_pdf_path = tmp_file.name

    images = convert_from_path(temp_pdf_path, 300)  # 300 DPI
    image_paths = []
    for i, image in enumerate(
        images
    ):  # TODO: slicing images to save money while testing lmao
        image_path = deck_dir / f"{i}.jpg"

        # Resize the image to 512x512 pixels
        resized_image = resize_image(image)
        with open(image_path, "wb") as f:
            f.write(resized_image.getvalue())

        image_paths.append(image_path)

    # Optional: Remove the temporary PDF file if not needed anymore
    os.remove(temp_pdf_path)

    return image_paths


def _generate_description_no_batch(pitch_deck_dir):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    all_images = sorted(pitch_deck_dir.iterdir())
    total_slides = len(all_images)
    all_descriptions = []
    print("pitch_deck_dir", pitch_deck_dir)
    print("total_slides", total_slides)
    print("all_images", all_images)
    for index, image_path in enumerate(all_images):
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        prompt_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Please provide a detailed description of slide {index + 1} in this pitch deck. Be sure to add key info as to what the slides talk about if you can.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high",
                    },
                },
            ],
        }

        try:
            data = client.chat.completions.create(
                model="gpt-4-vision-preview", messages=[prompt_message], max_tokens=300
            )
            description = data.choices[0].message.content
            all_descriptions.append(description)
            print(f"Description for slide {index + 1} is: {description}")
        except Exception as e:
            print(e)
            continue

        # Sleep for 5 seconds after every 3 calls
        if (index + 1) % 3 == 0:
            time.sleep(5)

    # Combine all descriptions into one string
    full_description = "\n\n".join(all_descriptions)

    # Save the combined description in the descriptions directory
    description_path = descriptions_dir / pitch_deck_dir.stem
    description_path.mkdir(parents=True, exist_ok=True)
    with open(description_path / "description.txt", "w") as desc_file:
        desc_file.write(full_description)

    return {
        "description": full_description,
        "file_path": description_path / "description.txt",
    }


def _generate_description(pitch_deck_dir, slides_per_batch=5):
    all_images = sorted(pitch_deck_dir.iterdir())
    total_slides = len(all_images)
    num_batches = max(1, total_slides // slides_per_batch)
    print("all_images", all_images)
    print("pitch_deck_dir", pitch_deck_dir)
    print("slides_per_batch", slides_per_batch)
    print("total_slides", total_slides)
    all_descriptions = []
    # return True
    for batch_num in range(num_batches):
        print(" === BATCH", batch_num, "=== ")
        start_index = batch_num * slides_per_batch
        end_index = start_index + slides_per_batch
        batch_images = all_images[start_index:end_index]
        print("batch_images", batch_images)

        base64_images = []
        for image_path in batch_images:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                base64_images.append(f"data:image/jpeg;base64,{base64_image}")

        prompt_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please provide a detailed description of slides {start_index + 1} to {min(end_index, total_slides)} in this pitch deck. Be sure to add key info as to what the slides tlak about if you can.",
                    },
                    *[
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_image, "detail": "high"},
                        }
                        for base64_image in base64_images
                    ],
                ],
            },
        ]
        print(base64_images[0])

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            data = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=prompt_messages,
                # max_tokens=300,
            )

            description = data.choices[0].message.content
            print("description", description)
            all_descriptions.append(description)
        except Exception as e:
            print(e)
            continue

    # Combine all descriptions into one string
    full_description = "\n\n".join(all_descriptions)

    # Save the combined description in the descriptions directory
    description_path = descriptions_dir / pitch_deck_dir.stem
    description_path.mkdir(parents=True, exist_ok=True)
    with open(description_path / "description.txt", "w") as desc_file:
        desc_file.write(full_description)

    return {
        "description": full_description,
        "file_path": description_path / "description.txt",
    }


def analyze_pitch_deck(pitch_deck_file_path):
    analysis_results = _generate_description_no_batch(pitch_deck_file_path)
    return analysis_results
