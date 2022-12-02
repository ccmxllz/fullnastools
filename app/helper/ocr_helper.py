import base64

from app.utils import RequestUtils
from config import DEFAULT_OCR_SERVER


class OcrHelper:

    _ocr_b64_url = "%s/captcha/base64" % DEFAULT_OCR_SERVER

    def __init__(self):
        pass

    def get_captcha_text(self, image_url, cookie=None, ua=None):
        """
        根据图片地址，获取验证码图片，并识别内容
        """
        if not image_url:
            return ""
        text = ""
        ret = RequestUtils(cookies=cookie, headers=ua).get_res(image_url)
        if ret is not None:
            image_bin = ret.content
            if not image_bin:
                return ""
            ret = RequestUtils().post_res(url=self._ocr_b64_url,
                                          json={"base64_img": base64.b64encode(image_bin).decode()})
            if ret:
                return ret.json().get("result")
        return text
