import logging
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

LIST_DISABLED_URL = os.getenv('LIST_DISABLED_URL')
DELETE_CUSTOMER_URL = os.getenv('DELETE_CUSTOMER_URL')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_DL')

class CustomLogger:
    """class responsible for handaling logs
       to use add to relevant functions:
       logger = CustomLogger(step="string", log_name="string").get_logger()
       logger.debug("this is the log line")"""


    def __init__(self, step, log_name, log_directory='/ghost_accounts/logs'):
        self.step = step
        self.log_name = log_name
        self.log_directory = log_directory
        self.logger = logging.getLogger(step)
        self._setup()

    def _setup(self):
        # Create log directory if it does not exist
        if not os.path.exists(self.log_directory):
            os.mkdir(self.log_directory)

        log_path = os.path.join(self.log_directory, f'{self.log_name}.log')
        if not self.logger.hasHandlers():
            file_handler = logging.FileHandler(log_path)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            #  for console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            #
            self.logger.setLevel(logging.DEBUG)

    def get_logger(self):
        return self.logger

class GhostsAccounts:
    """class responsible for handeling ghosts accounts to be deleted"""
    def __init__(self, list_disabled_url, delete_customer_url):
        self.list_disabled_url = list_disabled_url
        self.delete_customer_url = delete_customer_url

    def get_disabled_accounts(self):
        logger = CustomLogger(step="getAccounts", log_name="get_ghost_accounts").get_logger()
        try:
            response = requests.get(self.list_disabled_url)
            response.raise_for_status()
            data = response.json()

            count = data.get('count')
            customer_ids = data.get('results', [])
            if count != len(customer_ids):
                logger.error(f"Count mismatch")
                raise ValueError(f"Count mismatch")
            logger.debug("count and customer ID's are matching")
            return customer_ids
        except Exception as e:
            logger.error(f"Error fetching disabled accounts: {e}")
            raise

    def delete_account(self, customer_id):
        logger = CustomLogger(step="delete_accounts", log_name="delete_ghost_accounts").get_logger()
        try:
            delete_response = requests.post(self.delete_customer_url, json={"customer-id": customer_id})
            delete_status = delete_response.json().get('status')
            match delete_status:
                case 'success':
                    logger.info(f"Successfully deleted {customer_id}")
                case 'failed':
                    logger.error(f"Failed to delete {customer_id}")
                case 'nonexists':
                    logger.warning(f"{customer_id} does not exist")
        except Exception as e:
            logging.error(f"Error deleting {customer_id}: {e}")


def send_email(subject, body, to_email, from_email, smtp_server, attachment_paths):
    # Create the email container
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Attach the body text
    msg.attach(MIMEText(body, 'plain'))

    # Attach files
    for path in attachment_paths:
        part = MIMEBase('application', 'octet-stream')
        try:
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={path.split("/")[-1]}')
            msg.attach(part)
        except Exception as e:
            print(f"Could not attach file {path}: {e}")

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server) as server:
        server.sendmail(from_email, to_email, msg.as_string())

if __name__ == '__main__':
    logger = CustomLogger(step="devops", log_name="wrapper").get_logger()
    logger.debug("staring ghosts account actions")
    init = GhostsAccounts(LIST_DISABLED_URL,DELETE_CUSTOMER_URL)
    try:
        customer_ids = init.get_disabled_accounts()
        deleted = 0
        for customer_id in customer_ids:
            logger.debug(f'deleting {customer_id}')
            init.delete_account(customer_id)
            deleted += 1
        logger.info(f"script completed {deleted} accounts were deleted")
        body = f"script completed {deleted} accounts were deleted"
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        body = "failure to delete accounts check logs for more info"
    #  email notification
    subject = "ghost accounts automation report"
    to_email = "email@distribution.list"
    from_email = "devops@service.account"
    smtp_server = "smtp.server"
    attachment_paths = ["/ghost_accounts/logs"]
    send_email(subject, body, to_email, from_email, smtp_server, attachment_paths)
