from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math

def generate_image_with_obstacles(text_line, font_path, background_image_path, output_folder, image_index):
    """
    สร้างรูปภาพขนาด 400x400 พิกเซล พร้อมพื้นหลัง, ข้อความที่มีการปรับแต่ง (สี, เอียง, เบลอ),
    และเพิ่มอุปสรรคให้กับพื้นหลัง (เบลอ)

    Args:
        text_line (str): ข้อความที่ต้องการเรนเดอร์
        font_path (str): พาธไปยังไฟล์ฟอนต์ .ttf
        background_image_path (str): พาธไปยังไฟล์รูปภาพพื้นหลัง
        output_folder (str): โฟลเดอร์สำหรับบันทึกรูปภาพที่สร้างขึ้น
        image_index (int): ดัชนีสำหรับตั้งชื่อไฟล์รูปภาพเอาต์พุต
    Returns:
        tuple: (output_filename_relative, clean_text_line) หากสร้างสำเร็จ, มิฉะนั้น (None, None)
    """
    try:
        # 1. สร้างรูปภาพ 400x400 px และ 2. พื้นหลัง
        background = Image.open(background_image_path).convert("RGBA")
        target_size = (400, 400)
        background = background.resize(target_size, Image.Resampling.LANCZOS)
        width, height = background.size

        # 5. เพิ่มอุปสรรค เช่น เบลอรูปพื้นหลัง (Gaussian Blur)
        background = background.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 2.0))) 

        # 3. ใส่ตัวหนังสือ
        font_size = 100 
        font = ImageFont.truetype(font_path, font_size)

        # ใส่อุปสรรค: ใส่สีตัวหนังสือ (ทุกสี)
        text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255) 

        # คำนวณขนาดข้อความเริ่มต้น
        # สร้าง ImageDraw object ชั่วคราวเพื่อวัดขนาดข้อความ
        temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1))) 
        bbox = temp_draw.textbbox((0, 0), text_line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # ปรับขนาดฟอนต์ถ้าข้อความกว้าง/สูงเกินรูปภาพ พร้อมให้มีระยะขอบ
        while (text_width > width * 0.9 or text_height > height * 0.9) and font_size > 10:
            font_size -= 5
            font = ImageFont.truetype(font_path, font_size)
            bbox = temp_draw.textbbox((0, 0), text_line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        # ตำแหน่งกึ่งกลาง
        x_center = (width - text_width) / 2
        y_center = (height - text_height) / 2

        # สร้างรูปภาพโปร่งใสสำหรับข้อความเท่านั้น เพื่อหมุนและเบลอ
        text_image = Image.new('RGBA', target_size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text((x_center, y_center), text_line, font=font, fill=text_color)

        # ใส่อุปสรรค: เอียงตัวหนังสือ
        angle = random.uniform(-15, 15) 
        rotated_text_image = text_image.rotate(angle, center=(width/2, height/2), expand=False, fillcolor=(0,0,0,0))
        
        # ใส่อุปสรรค: เบลอตัวหนังสือ
        text_blur_radius = random.uniform(0.0, 1.5) 
        if text_blur_radius > 0:
            rotated_text_image = rotated_text_image.filter(ImageFilter.GaussianBlur(radius=text_blur_radius))

        # วางรูปภาพข้อความที่หมุนและเบลอแล้วลงบนพื้นหลัง
        background.paste(rotated_text_image, (0, 0), rotated_text_image)

        # สร้างโฟลเดอร์เอาต์พุตหากยังไม่มี
        os.makedirs(output_folder, exist_ok=True)

        # 1. ตั้งชื่อไฟล์ให้เป็น ตัวหนังสือ_BG.png
        # ทำให้ข้อความชื่อไฟล์ปลอดภัยสำหรับชื่อไฟล์ (เช่น ลบอักขระพิเศษ)
        clean_text_for_filename = "".join(c for c in text_line if c.isalnum() or c in (' ', '_')).strip()
        clean_text_for_filename = clean_text_for_filename.replace(" ", "_")
        if not clean_text_for_filename: # หากข้อความเป็นอักขระพิเศษทั้งหมด
            clean_text_for_filename = f"image_{image_index}"

        # จำกัดความยาวชื่อไฟล์เพื่อหลีกเลี่ยงชื่อที่ยาวเกินไป
        max_filename_len = 50
        if len(clean_text_for_filename) > max_filename_len:
            clean_text_for_filename = clean_text_for_filename[:max_filename_len] + f"_{image_index}"
        else:
            clean_text_for_filename = f"{clean_text_for_filename}_{image_index}"


        output_filename = os.path.join(output_folder, f"{clean_text_for_filename}_BG.png")
        background.save(output_filename)
        print(f"สร้างแล้ว: {output_filename} สำหรับข้อความ: '{text_line.strip()}'")

        # ส่งคืนพาธไฟล์แบบสัมพันธ์และข้อความจริง
        return os.path.join("images", os.path.basename(output_filename)), text_line.strip()

    except FileNotFoundError as e:
        print(f"ข้อผิดพลาด: ไม่พบไฟล์ - {e}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    return None, None

# --- Configuration ---
TEXT_FILE = "thai.txt"
FONT_PATH = "Sarun's ThangLuang.ttf" # Make sure this file is in the same directory as your script
BACKGROUND_IMAGE_PATH = "BG/bg_1.jpg" # Make sure this path is correct
OUTPUT_FOLDER = "images" # เปลี่ยนชื่อโฟลเดอร์เอาต์พุตเป็น "images" ตามโครงสร้าง label

# --- Main execution ---
if __name__ == "__main__":
    if not os.path.exists(TEXT_FILE):
        print(f"Error: The text file '{TEXT_FILE}' was not found.")
    elif not os.path.exists(FONT_PATH):
        print(f"Error: The font file '{FONT_PATH}' was not found.")
    elif not os.path.exists(BACKGROUND_IMAGE_PATH):
        print(f"Error: The background image '{BACKGROUND_IMAGE_PATH}' was not found. Please check the 'BG' folder and file name.")
    else:
        with open(TEXT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        generated_data = []
        for i, line in enumerate(lines):
            clean_line = line.strip()
            if clean_line:
                # ส่ง background_image_path ไปด้วย (แก้ไขจากเดิมที่ใช้ BG/bg_1.jpg ตรงๆ)
                relative_path, text_content = generate_image_with_obstacles(
                    clean_line, FONT_PATH, BACKGROUND_IMAGE_PATH, OUTPUT_FOLDER, i + 1
                )
                if relative_path and text_content:
                    generated_data.append((relative_path, text_content))

        # 2., 3., 4. เขียน label Formatch เป็น 70/20/10
        random.shuffle(generated_data) # สุ่มลำดับข้อมูลก่อนแบ่ง

        total_samples = len(generated_data)
        train_count = math.ceil(total_samples * 0.70) # ปัดขึ้นเพื่อไม่ให้ train น้อยเกินไป
        val_count = math.ceil(total_samples * 0.20)
        # test_count = total_samples - train_count - val_count # ส่วนที่เหลือคือ test
        # ปรับ test_count ให้แน่ใจว่าผลรวมไม่เกิน total_samples และครอบคลุมทั้งหมด
        test_count = total_samples - train_count - val_count
        if test_count < 0: # กรณีที่ปัดขึ้นแล้วเกิน
            test_count = 0 
            if train_count + val_count > total_samples: # ปรับ val หรือ train ลงถ้าจำเป็น
                 val_count = total_samples - train_count
                 if val_count < 0:
                     val_count = 0
                     train_count = total_samples


        train_data = generated_data[:train_count]
        val_data = generated_data[train_count : train_count + val_count]
        test_data = generated_data[train_count + val_count :] # เอาส่วนที่เหลือทั้งหมดไปเป็น test

        # สร้างโฟลเดอร์สำหรับ labels ถ้ายังไม่มี
        labels_folder = "labels"
        os.makedirs(labels_folder, exist_ok=True)

        with open(os.path.join(labels_folder, "train.txt"), 'w', encoding='utf-8') as f:
            for path, text in train_data:
                f.write(f"{path}\t{text}\n")
        print(f"สร้างไฟล์ 'train.txt' แล้ว ({len(train_data)} รายการ)")

        with open(os.path.join(labels_folder, "val.txt"), 'w', encoding='utf-8') as f:
            for path, text in val_data:
                f.write(f"{path}\t{text}\n")
        print(f"สร้างไฟล์ 'val.txt' แล้ว ({len(val_data)} รายการ)")

        with open(os.path.join(labels_folder, "test.txt"), 'w', encoding='utf-8') as f:
            for path, text in test_data:
                f.write(f"{path}\t{text}\n")
        print(f"สร้างไฟล์ 'test.txt' แล้ว ({len(test_data)} รายการ)")