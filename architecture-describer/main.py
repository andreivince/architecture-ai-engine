import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

image_folder = "images"
output_folder = "descriptions"

os.makedirs(output_folder, exist_ok=True)

supported_exts = [".jpg", ".jpeg", ".png"]

for filename in os.listdir(image_folder):
    if any(filename.lower().endswith(ext) for ext in supported_exts):
        image_path = os.path.join(image_folder, filename)
        print(f"Processing {filename}...")

        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode("utf-8")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Generate a prompt for this architectural structure in such detail so that an artificial intelligence model can reproduce this exact building."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            prompt = response.choices[0].message.content

            if prompt is not None:
                output_path = os.path.join(output_folder, filename + ".txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(prompt)

                print(f"Saved description to {output_path}\n")
            else:
                print(f"⚠️ No response received for {filename}. Skipping.\n")

        except Exception as e:
            print(f"Error processing {filename}: {e}\n")
