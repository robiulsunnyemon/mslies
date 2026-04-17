import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("\nListing models available for embedContent:")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"Name: {m.name}, Display Name: {m.display_name}")

print("\nListing models available for generateContent:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Name: {m.name}, Display Name: {m.display_name}")
