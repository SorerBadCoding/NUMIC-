import base64
from io import BytesIO

import qrcode


def generate_qr_data_uri(data: str) -> str:
    img = qrcode.make(data, box_size=8, border=1)
    buf = BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
