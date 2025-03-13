import requests
import logging
from datetime import datetime

# تنظیمات اولیه لاگ‌گیری
logging.basicConfig(
    filename="sms.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class APIError(Exception):
    """کلاس اختصاصی برای مدیریت خطاهای API"""
    
    def __init__(self, message, status_code=None):
        """
        مقداردهی اولیه خطا
        :param message: پیام خطا
        :param status_code: کد وضعیت HTTP (در صورت وجود)
        """
        super().__init__(message)
        self.status_code = status_code

    def __str__(self):
        """بازگرداندن پیام خطا به‌همراه کد وضعیت (در صورت وجود)"""
        if self.status_code:
            return f"APIError {self.status_code}: {self.args[0]}"
        return f"APIError: {self.args[0]}"


def fetch_data(url):
    """ارسال درخواست به API و مدیریت خطاها"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # اگر وضعیت پاسخ غیر 200 باشد، خطا ایجاد می‌کند
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError("درخواست به API ناموفق بود", status_code=response.status_code if 'response' in locals() else None) from e

# --- تست کلاس ---
try:
    data = fetch_data("https://api.example.com/data")
    print("داده دریافت شد:", data)
except APIError as e:
    print(e)


class SMSClient:
    """کلاس برای ارسال و مدیریت پیامک‌ها از طریق API سرویس SMS.ir"""
    
    BASE_URL = "https://api.sms.ir/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "x-api-key": self.api_key,
        })

    def _request(self, method, endpoint, data=None):
        """متد کمکی برای ارسال درخواست به API"""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.request(method, url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"خطا در درخواست به {url}: {e}")
            raise APIError(f"API request failed: {e}")

    def send_sms(self, mobile, template_id, parameters):
        """
        ارسال پیامک تاییدی به یک شماره خاص
        :param mobile: شماره موبایل گیرنده
        :param template_id: شناسه قالب پیامک
        :param parameters: لیست پارامترهای قالب
        :return: پاسخ API
        """
        data = {"mobile": mobile, "templateId": template_id, "parameters": parameters}
        response = self._request("POST", "send/verify", data)
        logging.info(f"پیامک به {mobile} ارسال شد. وضعیت: {response}")
        return response

    def send_bulk_sms(self, mobiles, template_id, parameters):
        """
        ارسال پیامک به چندین شماره همزمان
        :param mobiles: لیست شماره‌ها
        :param template_id: شناسه قالب پیامک
        :param parameters: لیست پارامترهای قالب
        :return: لیستی از پاسخ‌های API
        """
        results = {mobile: self.send_sms(mobile, template_id, parameters) for mobile in mobiles}
        return results

    def check_credit(self):
        """
        بررسی موجودی اعتبار پنل پیامک
        :return: مقدار اعتبار
        """
        response = self._request("GET", "credit")
        credit = response.get("credit")
        logging.info(f"اعتبار پنل: {credit}")
        return credit

    def schedule_sms(self, mobile, template_id, parameters, send_time):
        """
        زمان‌بندی ارسال پیامک برای یک زمان مشخص در آینده
        :param mobile: شماره گیرنده
        :param template_id: شناسه قالب پیامک
        :param parameters: لیست پارامترهای قالب
        :param send_time: زمان ارسال (datetime)
        :return: پاسخ API
        """
        if not isinstance(send_time, datetime):
            raise ValueError("فرمت زمان ارسال باید یک شیء datetime باشد.")
        
        formatted_time = send_time.strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "mobile": mobile,
            "templateId": template_id,
            "parameters": parameters,
            "sendDateTime": formatted_time
        }
        response = self._request("POST", "send/schedule", data)
        logging.info(f"پیامک زمان‌بندی شد برای {formatted_time}. وضعیت: {response}")
        return response

    def get_sms_status(self, message_id):
        """
        دریافت وضعیت پیامک ارسال‌شده
        :param message_id: شناسه پیامک
        :return: وضعیت پیامک
        """
        response = self._request("GET", f"sms/status/{message_id}")
        status = response.get("status")
        logging.info(f"وضعیت پیامک {message_id}: {status}")
        return status

def get_sent_messages(self, page=1, per_page=10):
    """
    دریافت لیست پیامک‌های ارسال‌شده
    :param page: شماره صفحه (پیش‌فرض 1)
    :param per_page: تعداد پیامک‌ها در هر صفحه (پیش‌فرض 10)
    :return: لیست پیامک‌ها
    """
    response = self._request("GET", f"sms/sent?page={page}&per_page={per_page}")
    messages = response.get("messages", [])
    logging.info(f"دریافت {len(messages)} پیامک ارسال‌شده از صفحه {page}")
    return messages

def cancel_scheduled_sms(self, message_id):
    """
    لغو پیامک زمان‌بندی‌شده
    :param message_id: شناسه پیامک زمان‌بندی‌شده
    :return: وضعیت لغو
    """
    response = self._request("DELETE", f"sms/schedule/{message_id}")
    logging.info(f"پیامک {message_id} لغو شد. وضعیت: {response}")
    return response

def get_delivery_report(self, message_id):
    """
    دریافت گزارش تحویل پیامک
    :param message_id: شناسه پیامک
    :return: وضعیت تحویل پیامک
    """
    response = self._request("GET", f"sms/delivery/{message_id}")
    delivery_status = response.get("status")
    logging.info(f"گزارش تحویل پیامک {message_id}: {delivery_status}")
    return delivery_status

def send_sms_with_custom_template(self, mobile, template_id, **kwargs):
    """
    ارسال پیامک با الگوی متغیر
    :param mobile: شماره گیرنده
    :param template_id: شناسه قالب پیامک
    :param kwargs: پارامترهای متغیر (نام متغیرها و مقدارشان)
    :return: پاسخ API
    """
    parameters = [{"name": key, "value": str(value)} for key, value in kwargs.items()]
    return self.send_sms(mobile, template_id, parameters)

response = client.send_sms_with_custom_template("09123456789", 12345, CODE="789654", NAME="Ali")
print("نتیجه ارسال پیامک با متغیرهای سفارشی:", response)

def send_bulk_sms_with_different_values(self, messages):
    """
    ارسال پیامک به چندین شماره، هرکدام با مقادیر متفاوت
    :param messages: لیستی از دیکشنری‌ها شامل 'mobile', 'template_id' و 'parameters'
    :return: نتایج ارسال پیامک‌ها
    """
    results = {}
    for msg in messages:
        mobile = msg.get("mobile")
        template_id = msg.get("template_id")
        parameters = msg.get("parameters", [])
        results[mobile] = self.send_sms(mobile, template_id, parameters)
    return results

messages = [
    {"mobile": "09123456789", "template_id": 12345, "parameters": [{"name": "CODE", "value": "111111"}]},
    {"mobile": "09351234567", "template_id": 12345, "parameters": [{"name": "CODE", "value": "222222"}]},
]
response = client.send_bulk_sms_with_different_values(messages)
print("نتایج ارسال گروهی با مقادیر مختلف:", response)

def get_recent_sms_reports(self, hours=24):
    """
    دریافت گزارش پیامک‌های ارسال‌شده در ۲۴ ساعت گذشته
    :param hours: تعداد ساعت گذشته برای دریافت گزارش (پیش‌فرض ۲۴ ساعت)
    :return: لیست پیامک‌های ارسال‌شده اخیر
    """
    response = self._request("GET", f"sms/reports?last_hours={hours}")
    messages = response.get("messages", [])
    logging.info(f"گزارش {len(messages)} پیامک اخیر دریافت شد.")
    return messages

recent_reports = client.get_recent_sms_reports()
print("گزارش پیامک‌های اخیر:", recent_reports)

def check_invalid_numbers(self, numbers):
    """
    بررسی شماره‌های غیرفعال یا مسدود شده
    :param numbers: لیست شماره‌های موبایل
    :return: شماره‌های نامعتبر
    """
    response = self._request("POST", "sms/check-invalid", {"numbers": numbers})
    invalid_numbers = response.get("invalid_numbers", [])
    logging.info(f"شماره‌های نامعتبر: {invalid_numbers}")
    return invalid_numbers

invalid_numbers = client.check_invalid_numbers(["09123456789", "09351234567"])
print("شماره‌های نامعتبر:", invalid_numbers)

def send_test_sms(self, mobile, template_id, parameters):
    """
    ارسال پیامک تستی بدون مصرف اعتبار پنل
    :param mobile: شماره گیرنده
    :param template_id: شناسه قالب پیامک
    :param parameters: لیست پارامترهای قالب
    :return: پاسخ API
    """
    response = self._request("POST", "sms/send-test", {
        "mobile": mobile, "templateId": template_id, "parameters": parameters
    })
    logging.info(f"پیامک تستی به {mobile} ارسال شد. وضعیت: {response}")
    return response

test_response = client.send_test_sms(
    "09123456789", 12345, [{"name": "CODE", "value": "999999"}]
)
print("نتیجه ارسال تستی:", test_response)


if __name__ == "__main__":
    API_KEY = "YOURAPIKEY"
    client = SMSClient(API_KEY)

    # ۱. ارسال پیامک به یک شماره
    response = client.send_sms(
        mobile="09123456789",
        template_id=12345,
        parameters=[{"name": "CODE", "value": "000000"}]
    )
    print("نتیجه ارسال تکی:", response)

    # ۲. ارسال پیامک به چندین شماره با مقادیر متفاوت
    messages = [
        {"mobile": "09123456789", "template_id": 12345, "parameters": [{"name": "CODE", "value": "111111"}]},
        {"mobile": "09351234567", "template_id": 12345, "parameters": [{"name": "CODE", "value": "222222"}]},
    ]
    bulk_response = client.send_bulk_sms_with_different_values(messages)
    print("نتیجه ارسال گروهی با مقادیر مختلف:", bulk_response)

    # ۳. دریافت گزارش پیامک‌های ارسال‌شده در ۲۴ ساعت گذشته
    recent_reports = client.get_recent_sms_reports()
    print("گزارش پیامک‌های اخیر:", recent_reports)

    # ۴. بررسی شماره‌های نامعتبر (مسدود شده یا غیرفعال)
    invalid_numbers = client.check_invalid_numbers(["09123456789", "09351234567"])
    print("شماره‌های نامعتبر:", invalid_numbers)

    # ۵. ارسال پیامک تستی بدون مصرف اعتبار پنل
    test_response = client.send_test_sms(
        "09123456789", 12345, [{"name": "CODE", "value": "999999"}]
    )
    print("نتیجه ارسال تستی:", test_response)

    # ۶. دریافت گزارش تحویل پیامک خاص
    delivery_status = client.get_delivery_report("1234567890")  # شناسه پیامک فرضی
    print("وضعیت تحویل پیامک:", delivery_status)

    # ۷. لغو پیامک زمان‌بندی‌شده
    cancel_status = client.cancel_scheduled_sms("1234567890")  # شناسه پیامک فرضی
    print("وضعیت لغو پیامک:", cancel_status)

    # ۸. بررسی اعتبار پنل پیامک
    credit = client.check_credit()
    print("اعتبار پنل:", credit)
