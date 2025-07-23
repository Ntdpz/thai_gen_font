from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math

def generate_image_with_obstacles(text_line, font_path, background_image_path, output_folder, image_index):
    """
    สร้างรูปภาพขนาด 400x400 พิกเซล พร้อมพื้นหลัง, ข้อความที่มีการปรับแต่ง (สี, เอียง, เบลอ, สุ่มขนาด),
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
        # ใส่อุปสรรค: สุ่มขนาดตัวหนังสือเริ่มต้น (20 ถึง 300)
        font_size = random.randint(20, 300) 
        font = ImageFont.truetype(font_path, font_size)

        # ใส่อุปสรรค: ใส่สีตัวหนังสือ (ทุกสี)
        text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255) 

        # คำนวณขนาดข้อความเริ่มต้น (ยังไม่หมุน) เพื่อใช้ในการปรับขนาดฟอนต์
        temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1))) 
        bbox_unrotated = temp_draw.textbbox((0, 0), text_line, font=font)
        text_width_unrotated = bbox_unrotated[2] - bbox_unrotated[0]
        text_height_unrotated = bbox_unrotated[3] - bbox_unrotated[1]

        # ปรับขนาดฟอนต์ถ้าข้อความกว้าง/สูงเกินรูปภาพ พร้อมให้มีระยะขอบ
        # กำหนดขีดจำกัดสูงสุดที่ข้อความสามารถครอบครองได้ (เช่น 95% ของรูปภาพ)
        # และเพิ่มเงื่อนไขการลดขนาดฟอนต์ที่รุนแรงขึ้นเมื่อฟอนต์ใหญ่มาก
        max_text_dimension = max(width, height) * 0.95 
        min_font_size = 5 

        # --- ปรับปรุงลูปการลดขนาดฟอนต์เริ่มต้น ---
        # ลดขนาดฟอนต์ลงเร็วขึ้นหากฟอนต์เริ่มต้นใหญ่มาก เพื่อให้มีพื้นที่เผื่อการหมุน
        while ((text_width_unrotated > max_text_dimension or 
                text_height_unrotated > max_text_dimension) or 
               font_size > 200) and font_size > min_font_size: # ลดขนาดมากขึ้นถ้าเริ่มต้นใหญ่มาก
            font_size -= 5 # ลองลดขนาดทีละมากขึ้นเมื่อฟอนต์ใหญ่
            if font_size < min_font_size:
                font_size = min_font_size
            font = ImageFont.truetype(font_path, font_size)
            bbox_unrotated = temp_draw.textbbox((0, 0), text_line, font=font)
            text_width_unrotated = bbox_unrotated[2] - bbox_unrotated[0]
            text_height_unrotated = bbox_unrotated[3] - bbox_unrotated[1]
        
        # --- เตรียม Canvas สำหรับข้อความที่หมุนได้โดยไม่ขาด ---
        # ขนาด Canvas ที่ปลอดภัยคือขนาดทแยงมุมของรูปภาพ 400x400
        diagonal_size = int(math.sqrt(width**2 + height**2))
        expanded_canvas_size = (diagonal_size, diagonal_size)

        # สร้างรูปภาพโปร่งใสสำหรับข้อความเท่านั้น ด้วยขนาดที่ใหญ่กว่าเดิม
        text_image = Image.new('RGBA', expanded_canvas_size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_image)

        # --- เพิ่ม Padding ใน Canvas เริ่มต้น ---
        # คำนวณตำแหน่งข้อความบน text_image ที่ใหญ่ขึ้น (ต้องอยู่กึ่งกลางของ canvas ใหม่)
        # และเพิ่ม padding รอบข้อความบน canvas นี้
        canvas_padding = int(expanded_canvas_size[0] * 0.02) # เพิ่มขอบ 2% ของขนาด canvas
        x_text_on_expanded_image = (expanded_canvas_size[0] - text_width_unrotated) / 2
        y_text_on_expanded_image = (expanded_canvas_size[1] - text_height_unrotated) / 2
        
        # วาดข้อความลงบน text_image ที่มี padding
        text_draw.text((x_text_on_expanded_image, y_text_on_expanded_image), text_line, font=font, fill=text_color)

        # ใส่อุปสรรค: เอียงตัวหนังสือ
        angle = random.uniform(-15, 15) 
        # หมุนรูปภาพข้อความรอบจุดกึ่งกลางของ text_image เอง
        # *** ใช้ expand=True เพื่อให้ภาพที่หมุนแล้วไม่ถูกตัดขาด ***
        rotated_text_image = text_image.rotate(angle, center=(expanded_canvas_size[0]/2, expanded_canvas_size[1]/2), expand=True, fillcolor=(0,0,0,0))
        
        # ใส่อุปสรรค: เบลอตัวหนังสือ
        text_blur_radius = random.uniform(0.0, 1.5) 
        if text_blur_radius > 0:
            rotated_text_image = rotated_text_image.filter(ImageFilter.GaussianBlur(radius=text_blur_radius))

        # --- ปรับขนาดและวางตำแหน่งบนพื้นหลัง 400x400 ---
        # 1. หาขอบเขตของเนื้อหาข้อความจริงๆ หลังจากหมุนและเบลอแล้ว (ไม่รวมส่วนโปร่งใส)
        rotated_bbox_content = rotated_text_image.getbbox()

        if rotated_bbox_content: 
            # 2. Crop รูปภาพ rotated_text_image ให้เหลือแต่ส่วนที่มีเนื้อหาจริงๆ
            cropped_rotated_text_image = rotated_text_image.crop(rotated_bbox_content)

            # 3. คำนวณขนาดของเนื้อหาที่ถูก crop แล้ว
            final_content_width = cropped_rotated_text_image.width
            final_content_height = cropped_rotated_text_image.height

            # 4. ปรับขนาดของ cropped_rotated_text_image ให้พอดีกับกรอบ 400x400 โดยไม่ให้ล้น
            #    ใช้ scale_factor เพื่อย่อขนาดเท่านั้น (ถ้าใหญ่กว่า) โดยเผื่อขอบ 15% (เหลือ 85% สำหรับตัวอักษร)
            final_max_fit_width = width * 0.85 
            final_max_fit_height = height * 0.85

            scale_factor = 1.0
            if final_content_width > final_max_fit_width:
                scale_factor = min(scale_factor, final_max_fit_width / final_content_width)
            if final_content_height > final_max_fit_height:
                scale_factor = min(scale_factor, final_max_fit_height / final_content_height)
            
            if scale_factor < 1.0: # ถ้าต้องย่อขนาด
                new_content_width = int(final_content_width * scale_factor)
                new_content_height = int(final_content_height * scale_factor)
                # ตรวจสอบขนาดขั้นต่ำเพื่อป้องกันข้อผิดพลาด
                if new_content_width < 1: new_content_width = 1
                if new_content_height < 1: new_content_height = 1

                cropped_rotated_text_image = cropped_rotated_text_image.resize((new_content_width, new_content_height), Image.Resampling.LANCZOS)
            
            # อัปเดตขนาดที่ใช้คำนวณตำแหน่ง (หลังจากอาจมีการย่อ)
            final_content_width = cropped_rotated_text_image.width
            final_content_height = cropped_rotated_text_image.height

            # 5. คำนวณตำแหน่งที่จะวาง cropped_rotated_text_image บน background 400x400 ให้กึ่งกลาง
            paste_x = int((width - final_content_width) / 2)
            paste_y = int((height - final_content_height) / 2)

            # 6. วางข้อความลงบนพื้นหลัง
            background.paste(cropped_rotated_text_image, (paste_x, paste_y), cropped_rotated_text_image)
        else:
            # กรณีที่ text_line ว่างเปล่าหรือ font_size เล็กจนมองไม่เห็น
            print(f"คำเตือน: ข้อความ '{text_line.strip()}' อาจเล็กเกินไปหรือมองไม่เห็น จึงไม่ได้ถูกวางลงบนรูปภาพ")
        # --- สิ้นสุดการแก้ไขการวางตำแหน่ง ---

        # สร้างโฟลเดอร์เอาต์พุตหากยังไม่มี
        os.makedirs(output_folder, exist_ok=True)

        # ตั้งชื่อไฟล์ให้เป็น ตัวหนังสือ_BG.png
        clean_text_for_filename = "".join(c for c in text_line if c.isalnum() or c in (' ', '_')).strip()
        clean_text_for_filename = clean_text_for_filename.replace(" ", "_")
        if not clean_text_for_filename: 
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

        return os.path.join("images", os.path.basename(output_filename)), text_line.strip()

    except FileNotFoundError as e:
        print(f"ข้อผิดพลาด: ไม่พบไฟล์ - {e}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    return None, None

# --- Configuration ---
TEXT_FILE = "thai.txt"
FONT_PATH = "Sarun's ThangLuang.ttf" # ตรวจสอบให้แน่ใจว่าไฟล์นี้อยู่ในไดเรกทอรีเดียวกัน
BACKGROUND_IMAGE_PATH = "BG/bg_1.jpg" # ตรวจสอบให้แน่ใจว่าพาธนี้ถูกต้อง
OUTPUT_FOLDER = "images" # โฟลเดอร์สำหรับบันทึกรูปภาพที่สร้างขึ้น

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
                relative_path, text_content = generate_image_with_obstacles(
                    clean_line, FONT_PATH, BACKGROUND_IMAGE_PATH, OUTPUT_FOLDER, i + 1
                )
                if relative_path and text_content:
                    generated_data.append((relative_path, text_content))

        # เขียน label Formatch เป็น 70/20/10
        random.shuffle(generated_data) 

        total_samples = len(generated_data)
        train_count = math.ceil(total_samples * 0.70) 
        val_count = math.ceil(total_samples * 0.20)
        # คำนวณ test_count จากส่วนที่เหลือเพื่อให้แน่ใจว่าผลรวมเท่ากับ total_samples
        test_count = total_samples - train_count - val_count
        
        # ป้องกันกรณีที่การปัดเศษทำให้ผลรวมเกิน หรือเหลือติดลบ
        if test_count < 0:
            test_count = 0
            if train_count + val_count > total_samples:
                # ถ้า val_count เกิน ให้ลด val_count ลงก่อน
                val_count = total_samples - train_count
                if val_count < 0: # ถ้า train_count อย่างเดียวก็เกินแล้ว
                    val_count = 0
                    train_count = total_samples # ให้ train_count เป็นทั้งหมด

        train_data = generated_data[:train_count]
        val_data = generated_data[train_count : train_count + val_count]
        test_data = generated_data[train_count + val_count :] 

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