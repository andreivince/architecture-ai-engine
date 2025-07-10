import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Set folders
image_folder = "images"
output_folder = "descriptions"

os.makedirs(output_folder, exist_ok=True)

supported_exts = [".jpg", ".jpeg", ".png"]

# Loop through all images
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
                            You must:

                                1. Describe only the visible geometry — avoid assumptions about materials, lighting, or environment.

                                2. Use strict architectural vocabulary: massing, voids, modules, volumetric stacking, cantilevers, setbacks, grids, and hierarchical forms.

                                3. Focus on spatial composition:

                                    - Quantify floor count and any volumetric hierarchy.

                                    - Describe presence and placement of voids, cut-outs, or recesses in the massing.

                                    - State the number and rhythm of grid subdivisions across each elevation.

                                    - Call out projecting, recessed, or floating elements.

                                4. Emphasize voids and negative space:

                                    - If large cutouts penetrate through the form, state: “rectilinear void interrupts the massing across [X] floors.”

                                    - For recessed terraces or frame-like voids, note their dimensions and positions explicitly.

                                5. Describe the ground floor as a distinct layer:

                                    - Mention if it's recessed, elevated, or set apart volumetrically.

                                    - If it features a continuous transparent base, write: “unbroken base with no vertical subdivision contrasts sharply with upper grid.”

                                6. Avoid any reference to materials, reflections, weather, or vegetation — focus on formal logic only.

                                7. Your final output must be a single structured paragraph, using direct, technical language to encode architectural relationships and form.

                                You must force the AI to understand volumetric articulation, void-based design logic, and rhythmic composition — without relying on surface or setting.

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
                # Save the prompt as text file
                output_path = os.path.join(output_folder, filename + ".txt")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(prompt)

                print(f"Saved description to {output_path}\n")

                # Now update corresponding JSON file
                number_str = filename.split('_')[1].split('.')[0]  # e.g., '0001'
                image_num = int(number_str) - 1  # convert to 0-based index for tower folders

                tower_folder = f"GeometryTowerImagesRhino/tower_{image_num:03d}"
                json_path = os.path.join(tower_folder, "params.json")

                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Replace the prompt
                    data["tower_info"]["prompt"] = prompt

                    # Save updated JSON
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"Updated prompt in {json_path}\n")
                else:
                    print(f"JSON file not found at {json_path}. Skipping JSON update.\n")

            else:
                print(f"No response received for {filename}. Skipping.\n")

        except Exception as e:
            print(f"Error processing {filename}: {e}\n")
