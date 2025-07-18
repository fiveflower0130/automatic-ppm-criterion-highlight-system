import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.header import Header
from typing import Dict, List
from app.utils.logger import Logger


class EmailClient:
    """電子郵件服務類別"""
    def __init__(self):
        self.__email_clients = {}
        self.__logger = Logger().get_logger()

    def __get_client(self, host: str) -> smtplib.SMTP:
        """取得 SMTP 客戶端"""
        return self.__email_clients[host]

    def __get_message(self, data: Dict) -> MIMEMultipart:
        """建立電子郵件訊息"""
        message = MIMEMultipart('alternative')
        message['From'] = data['from']['name']
        message['To'] = ",".join(data['to']) if data['to'] else None
        message['Cc'] = ",".join(data['cc']) if data['cc'] else None
        message['Bcc'] = ",".join(data['bcc']) if data['bcc'] else None
        message['Subject'] = Header(data['subject'], 'utf-8') if data['subject'] else Header('無標題', 'utf-8')

        # 添加郵件內容
        body = MIMEText(data['body'], 'html', 'utf-8') if data['body'] else MIMEText('<p>無內容</p>', 'html', 'utf-8')
        message.attach(body)

        # 添加附件
        for attach in data.get('attachment', []):
            ctype, encoding = mimetypes.guess_type(attach)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)

            with open(attach, "rb") as fp:
                if maintype == "text":
                    attachment = MIMEText(fp.read(), _subtype=subtype, _charset='utf-8')
                elif maintype == "image":
                    attachment = MIMEImage(fp.read(), _subtype=subtype)
                elif maintype == "audio":
                    attachment = MIMEAudio(fp.read(), _subtype=subtype)
                else:
                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(fp.read())
                    encoders.encode_base64(attachment)

            attachment["Content-Disposition"] = f'attachment; filename="{attach}"'
            message.attach(attachment)

        return message

    def add_client(self, host: str, port: str = '', user: str = '', pwd: str = ''):
        """新增 SMTP 客戶端"""
        try:
            client = smtplib.SMTP(f"{host}:{port}") if port else smtplib.SMTP(host)
            if user and pwd:
                client.login(user, pwd)
            self.__email_clients[host] = client
            self.__logger.info(f"成功新增 SMTP 客戶端: {host}")
        except smtplib.SMTPException as error:
            self.__logger.error(f"無法新增 SMTP 客戶端: {error}")

    def send_email(self, host: str, data: Dict):
        """發送電子郵件"""
        try:
            email_client = self.__get_client(host)
            sender = data['from']['email']
            receiver = data['to'] + data['cc'] + data['bcc']
            message = self.__get_message(data)
            email_client.sendmail(sender, receiver, message.as_string())
            self.__logger.info("郵件已成功發送")
        except smtplib.SMTPException as error:
            self.__logger.error(f"無法發送郵件: {error}")

    def delete_client(self, host: str):
        """刪除 SMTP 客戶端"""
        try:
            email_client = self.__email_clients.pop(host)
            email_client.quit()
            self.__logger.info(f"成功刪除 SMTP 客戶端: {host}")
        except smtplib.SMTPException as error:
            self.__logger.error(f"無法刪除 SMTP 客戶端: {error}")