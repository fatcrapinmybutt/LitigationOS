
import os

class Config:
    KOFI_VERIFICATION_TOKEN = os.environ.get("KOFI_VERIFICATION_TOKEN", "47bc8577-fc42-4059-bede-cbad26561a20")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Your Legal Services")
    SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@yourdomain.com")
    DOWNLOAD_BASE_URL = os.environ.get("DOWNLOAD_BASE_URL", "https://yourdomain.com/downloads/")

    @staticmethod
    def get_email_template_vars():
        return {
            'company_name': Config.COMPANY_NAME,
            'support_email': Config.SUPPORT_EMAIL,
            'year': 2024
        }
