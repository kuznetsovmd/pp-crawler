class CaptchaException(Exception):
    def __init__(self):
        super().__init__("The website has given out a captcha")
