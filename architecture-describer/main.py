import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

image_folder = "images_realism"
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
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """
                            You are a prompt engineer trained to extract architectural instructions from real images for use in image generation models. Your task is to observe the building and output a single paragraph prompt that causes a model like DALL·E, Midjourney, or SDXL to recreate it with maximum visual fidelity.

                            You must:

                            1. Describe only what is visible — do not assume or invent.
                            2. Use strict architectural terminology: façade, modules, mullions, spandrels, massing, glazing, rhythm.
                            3. For each element, **quantify with precision**. Include:
                            - Number of visible floors.
                            - Estimated height of ground floor vs others.
                            - Number of horizontal bays and vertical subdivisions per floor.
                            - Mullion thickness in cm if discernible.
                            - Presence or absence of spandrels or floor breaks.
                            - Whether any floor is clearly different from others (material, height, transparency).
                            4. Describe ground floor separately with emphasis:
                            - If it's double-height, say so explicitly.
                            - If it uses **larger uninterrupted glass panels**, emphasize: “NO vertical mullions or divisions on ground floor glazing.”
                            - Mention warm lighting, interior visibility, and volumetric distinction.
                            5. State clearly: “The ground floor MUST appear taller, with smooth, mullion-free glass different from the upper grid pattern.”
                            6. DO NOT assume the model will understand hierarchy — you must make contrasts explicit.
                            7. Final prompt must be one precise paragraph with all of the above baked in. No fluff. No soft words. Absolute clarity.

                            Your output must force the AI to **treat the base, grid, and massing differently** — or the generation will fail.
                            
                            If vertical mullions are visible on the upper floors but NOT on the ground floor, this **MUST** be explicitly stated in the prompt. Use phrases like: “uninterrupted transparent glazing at base” and “distinct visual transition.”

                            Begin.

                                    """
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
                print(f"No response received for {filename}. Skipping.\n")

        except Exception as e:
            print(f"Error processing {filename}: {e}\n")
