import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False, verbose=False, quantize=True)

def process_pdf_with_textract(pages):
    layout_json = {}
    word_json = {}

    for i, page in enumerate(pages):
        page_num = str(i)
        width, height = page.size

        layout_json[page_num] = {
            "image_name": f"page-{page_num}.jpg",
            "width": width,
            "height": height,
            "sections": []
        }

        word_json[page_num] = []

        sections = {
            "Title": [int(width * 0.1), int(height * 0.05), int(width * 0.9), int(height * 0.15)],
            "Table": [int(width * 0.1), int(height * 0.25), int(width * 0.9), int(height * 0.75)]
        }

        for region_class, region_box in sections.items():
            cropped = page.crop(region_box)
            cropped_np = np.array(cropped)

            results = reader.readtext(cropped_np, detail=1, paragraph=False, batch_size=16)

            text_buffer = []
            for (bbox, text, conf) in results:
                if not text.strip():
                    continue
                x1 = int(bbox[0][0] + region_box[0])
                y1 = int(bbox[0][1] + region_box[1])
                x2 = int(bbox[2][0] + region_box[0])
                y2 = int(bbox[2][1] + region_box[1])

                word_json[page_num].append({
                    "text": text,
                    "bbox": [x1, y1, x2, y2]
                })
                text_buffer.append(text)

            layout_json[page_num]["sections"].append({
                "bbox": [
                    region_box[0]/width,
                    region_box[1]/height,
                    region_box[2]/width,
                    region_box[3]/height
                ],
                "class": region_class,
                "score": 0.85,
                "text": " ".join(text_buffer)
            })

    return layout_json, word_json