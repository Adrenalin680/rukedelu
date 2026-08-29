from PIL import Image, ImageDraw, ImageFont
import os

# Создаем изображение
img = Image.new('RGB', (200, 200), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# Рисуем рамку
draw.rectangle([10, 10, 190, 190], outline='#f0b90b', width=4)

# Текст (упрощенный вариант)
try:
    font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    font_tiny = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
except:
    font_big = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_tiny = ImageFont.load_default()

draw.text((100, 70), "ДЕЛО", fill='#f0b90b', anchor='mt', font=font_big)
draw.text((100, 110), "В РУКИ", fill='white', anchor='mt', font=font_small)
draw.text((100, 150), "⚖️ ЮРИСТЫ РОССИИ", fill='#f0b90b', anchor='mt', font=font_tiny)

img.save('static/logo.png')
print("Логотип создан!")
