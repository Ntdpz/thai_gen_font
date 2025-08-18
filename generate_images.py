from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import math

def generate_image_with_obstacles(text_line, font_path, background_image_path, output_folder, image_index):
    """
    สร้างรูปภาพขนาด 400x400 พิกเซล พร้อมพื้นหลัง, ข้อความที่มีการปรับแต่ง (สี, เอียง XY สุ่มทิศทาง, เบลอ, สุ่มขนาด, เอียงแกน Z จำลอง),
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
        max_text_dimension = max(width, height) * 0.95 
        min_font_size = 5 

        # --- ปรับปรุงลูปการลดขนาดฟอนต์เริ่มต้น ---
        # ลดขนาดฟอนต์ลงเร็วขึ้นหากฟอนต์เริ่มต้นใหญ่มาก เพื่อให้มีพื้นที่เผื่อการหมุนและการบิดเบือน
        while ((text_width_unrotated > max_text_dimension or 
                text_height_unrotated > max_text_dimension) or 
               font_size > 200) and font_size > min_font_size:
            font_size -= 5 
            if font_size < min_font_size:
                font_size = min_font_size
            font = ImageFont.truetype(font_path, font_size)
            bbox_unrotated = temp_draw.textbbox((0, 0), text_line, font=font)
            text_width_unrotated = bbox_unrotated[2] - bbox_unrotated[0]
            text_height_unrotated = bbox_unrotated[3] - bbox_unrotated[1]
        
        # --- เตรียม Canvas สำหรับข้อความที่หมุนได้โดยไม่ขาด (รวมถึงการบิดเบือน) ---
        # ขนาด Canvas ที่ปลอดภัยคือขนาดทแยงมุมของรูปภาพ 400x400
        # เผื่อพื้นที่เพิ่มขึ้นอีกเล็กน้อยสำหรับ shear transform ที่อาจทำให้ภาพขยายใหญ่ขึ้น
        diagonal_size = int(math.sqrt(width**2 + height**2) * 1.3) # เพิ่ม 30% เพื่อรองรับ shear/perspective
        expanded_canvas_size = (diagonal_size, diagonal_size)

        # สร้างรูปภาพโปร่งใสสำหรับข้อความเท่านั้น ด้วยขนาดที่ใหญ่กว่าเดิม
        text_image = Image.new('RGBA', expanded_canvas_size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_image)

        x_text_on_expanded_image = (expanded_canvas_size[0] - text_width_unrotated) / 2
        y_text_on_expanded_image = (expanded_canvas_size[1] - text_height_unrotated) / 2
        
        text_draw.text((x_text_on_expanded_image, y_text_on_expanded_image), text_line, font=font, fill=text_color)

        # ใส่อุปสรรค: เอียงตัวหนังสือ (แกน XY)
        angle_xy = random.uniform(-15, 15) 
        rotated_text_image = text_image.rotate(angle_xy, center=(expanded_canvas_size[0]/2, expanded_canvas_size[1]/2), expand=True, fillcolor=(0,0,0,0))
        
        # --- จำลองการเอียงแกน Z โดยการบิดเบือน (Shearing) อย่างถูกต้อง ---
        apply_shear = random.random() < 0.7 # 70% ที่จะใช้ shear
        if apply_shear:
            # สุ่มทิศทางการเอียงทั้งแกน X และ Y (ทั้งบวกและลบ)
            shear_factor_x = random.uniform(-0.25, 0.25) # ลดช่วงเพื่อลดการขาด
            shear_factor_y = random.uniform(-0.25, 0.25) # ลดช่วงเพื่อลดการขาด

            # Apply ShearX transform matrix
            if abs(shear_factor_x) > 0.01: 
                rotated_text_image = rotated_text_image.transform(
                    rotated_text_image.size,
                    Image.Transform.AFFINE, # แก้ไข: เปลี่ยนจาก AFFine เป็น AFFINE
                    (1, shear_factor_x, 0, 0, 1, 0), # (a, b, c, d, e, f)
                    resample=Image.Resampling.BICUBIC
                )
            
            # Apply ShearY transform matrix
            if abs(shear_factor_y) > 0.01:
                 rotated_text_image = rotated_text_image.transform(
                    rotated_text_image.size,
                    Image.Transform.AFFINE, # แก้ไข: เปลี่ยนจาก AFFine เป็น AFFINE
                    (1, 0, 0, shear_factor_y, 1, 0), # (a, b, c, d, e, f)
                    resample=Image.Resampling.BICUBIC
                )

            # --- จำลองการเอียงแกน -Z โดยการปรับขนาดความสูง (Perspective Scaling แบบง่าย) ---
            apply_z_tilt = random.random() < 0.5 # โอกาส 50% ที่จะใช้ Z tilt
            if apply_z_tilt:
                current_width = rotated_text_image.width
                current_height = rotated_text_image.height

                if current_height > 10 and current_width > 10: # ป้องกัน error ถ้าขนาดน้อยเกินไป
                    # สุ่มว่าจะทำให้ด้านบน/ล่างเล็กลง หรือ ซ้าย/ขวาเล็กลง
                    top_or_bottom_tilt = random.choice(['top_smaller', 'bottom_smaller', 'left_smaller', 'right_smaller'])
                    z_scale_factor = random.uniform(0.75, 0.98) # ย่อขนาด 75-98%

                    if top_or_bottom_tilt in ['top_smaller', 'bottom_smaller']:
                        z_tilted_image = Image.new('RGBA', (current_width, current_height), (0, 0, 0, 0))
                        
                        for y in range(current_height):
                            scale_y = 1.0
                            if top_or_bottom_tilt == 'top_smaller':
                                # ด้านบนเล็กลง, ด้านล่างปกติ
                                scale_y = z_scale_factor + (1.0 - z_scale_factor) * (y / current_height)
                            else: # bottom_smaller
                                # ด้านล่างเล็กลง, ด้านบนปกติ
                                scale_y = 1.0 - (1.0 - z_scale_factor) * (y / current_height)
                            
                            new_row_width = int(current_width * scale_y)
                            if new_row_width > 0: # ตรวจสอบป้องกันขนาดเป็นศูนย์
                                row_offset_x = (current_width - new_row_width) // 2
                                
                                # Crop แถวเดียวและ resize
                                row_image = rotated_text_image.crop((0, y, current_width, y + 1))
                                row_image = row_image.resize((new_row_width, 1), Image.Resampling.LANCZOS)
                                z_tilted_image.paste(row_image, (row_offset_x, y))
                        rotated_text_image = z_tilted_image

                    elif top_or_bottom_tilt in ['left_smaller', 'right_smaller']:
                        # วิธีที่ง่ายกว่าคือหมุนภาพ 90 องศา, ทำ row-wise tilt, แล้วหมุนกลับ
                        temp_col_image = rotated_text_image.transpose(Image.Transpose.ROTATE_90)
                        temp_col_image_width, temp_col_image_height = temp_col_image.size
                        
                        tilted_temp_col_image = Image.new('RGBA', (temp_col_image_width, temp_col_image_height), (0,0,0,0))

                        for y_temp in range(temp_col_image_height): # y_temp ตรงกับ x เดิมของภาพต้นฉบับ
                            scale_along_y_temp = 1.0
                            if top_or_bottom_tilt == 'left_smaller': # 'left_smaller' ในภาพต้นฉบับคือ 'top_smaller' หลังหมุน 90
                                scale_along_y_temp = z_scale_factor + (1.0 - z_scale_factor) * (y_temp / temp_col_image_height)
                            else: # 'right_smaller' ในภาพต้นฉบับคือ 'bottom_smaller' หลังหมุน 90
                                scale_along_y_temp = 1.0 - (1.0 - z_scale_factor) * (y_temp / temp_col_image_height)
                            
                            new_row_width_temp = int(temp_col_image_width * scale_along_y_temp)
                            if new_row_width_temp > 0: # ตรวจสอบป้องกันขนาดเป็นศูนย์
                                row_offset_x_temp = (temp_col_image_width - new_row_width_temp) // 2
                                row_image_temp = temp_col_image.crop((0, y_temp, temp_col_image_width, y_temp + 1))
                                row_image_temp = row_image_temp.resize((new_row_width_temp, 1), Image.Resampling.LANCZOS)
                                tilted_temp_col_image.paste(row_image_temp, (row_offset_x_temp, y_temp))
                        
                        rotated_text_image = tilted_temp_col_image.transpose(Image.Transpose.ROTATE_270) # หมุนกลับไปทิศทางเดิม
                        
                        # หลังจากการหมุนกลับและบิดเบือน ควร re-evaluate bbox อีกครั้งเพื่อตัดส่วนเกิน
                        rotated_text_image_bbox = rotated_text_image.getbbox()
                        if rotated_text_image_bbox:
                            rotated_text_image = rotated_text_image.crop(rotated_text_image_bbox)
                        
                        # Resample ให้กลับมาเป็นขนาดเดิม (เพื่อไม่ให้ภาพใหญ่เกินไปเมื่อนำไปวาง)
                        # ใช้ขนาด original_width, original_height ที่ได้มาจากก่อน shear/z-tilt
                        rotated_text_image = rotated_text_image.resize((current_width, current_height), Image.Resampling.LANCZOS)


        # ใส่อุปสรรค: เบลอตัวหนังสือ
        text_blur_radius = random.uniform(0.0, 1.5) 
        if text_blur_radius > 0:
            rotated_text_image = rotated_text_image.filter(ImageFilter.GaussianBlur(radius=text_blur_radius))

        # --- ปรับขนาดและวางตำแหน่งบนพื้นหลัง 400x400 ---
        # หา bounding box ของเนื้อหาหลังจากการ transformation ทั้งหมด
        rotated_bbox_content = rotated_text_image.getbbox()

        if rotated_bbox_content: 
            # Crop รูปภาพให้เหลือเฉพาะเนื้อหา
            cropped_rotated_text_image = rotated_text_image.crop(rotated_bbox_content)

            final_content_width = cropped_rotated_text_image.width
            final_content_height = cropped_rotated_text_image.height

            # กำหนดขนาดสูงสุดที่ข้อความสามารถครอบครองได้บนภาพพื้นหลัง
            # ลดค่านี้ลงเพื่อให้มีขอบว่างมากขึ้น ป้องกันการขาด
            final_max_fit_width = width * 0.75 
            final_max_fit_height = height * 0.75

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

            # คำนวณตำแหน่งที่จะวาง cropped_rotated_text_image บน background 400x400 ให้กึ่งกลาง
            paste_x = int((width - final_content_width) / 2)
            paste_y = int((height - final_content_height) / 2)

            # 6. วางข้อความลงบนพื้นหลัง
            background.paste(cropped_rotated_text_image, (paste_x, paste_y), cropped_rotated_text_image)
        else:
            print(f"คำเตือน: ข้อความ '{text_line.strip()}' อาจเล็กเกินไปหรือมองไม่เห็น จึงไม่ได้ถูกวางลงบนรูปภาพ")

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
TEXT_FILE = "thai_dict_clean.txt"
FONT_PATH = "Sarun's ThangLuang.ttf" 
BACKGROUND_IMAGE_PATH = "BG/bg_1.jpg" 
OUTPUT_FOLDER = "images" 

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

        random.shuffle(generated_data) 

        total_samples = len(generated_data)
        train_count = math.ceil(total_samples * 0.70) 
        val_count = math.ceil(total_samples * 0.20)
        test_count = total_samples - train_count - val_count
        
        if test_count < 0:
            test_count = 0
            if train_count + val_count > total_samples:
                val_count = total_samples - train_count
                if val_count < 0:
                    val_count = 0
                    train_count = total_samples 

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