import requests
from PIL import Image
from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor

image_url = "https://storage.googleapis.com/video-tutorial-screenshots/eyeglasses-d44dfbcc-9908-448a-a11b-d3670cbcb095/screenshot_0.png"
image = Image.open(requests.get(image_url, stream=True).raw)

model = Pix2StructForConditionalGeneration.from_pretrained("google/pix2struct-screen2words-base")
processor = Pix2StructProcessor.from_pretrained("google/pix2struct-screen2words-base")

question = "Which project am I clicking on? (1) Bigeye (2) Caliza (3) Bytebase"

inputs = processor(images=image, text=question, return_tensors="pt")

predictions = model.generate(**inputs)
print(processor.decode(predictions[0], skip_special_tokens=True))