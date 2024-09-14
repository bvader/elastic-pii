import random
import datetime
from datetime import datetime, timezone
from faker import Faker
fake = Faker()

# Parameters 
LOG_NUM_LINES = 10000
LOG_FILE_NAME = "./pii.log"

# Define functions to generate random data (same as before)
# Define functions to generate random data
def generate_name():
  return fake.name()

def generate_email():
  return fake.ascii_email()

def generate_address():
  address = fake.address()
  clean_address = address.replace("\n", ", ")
  return clean_address

def generate_phone_number():
  return fake.phone_number()

def generate_org():
  orgs = ["Chase", "Capital One Bank", "Wells Fargo", "Citibank", "Bank of America", "PNC Bank", "Synchrony Bank", "Barclay's", "Huntington", "U.S. Bank", "TD Bank", "TD Bank", "Citizens Bank", "ACORNS", "Ally Bank", "SunTrust", "Bank of New York", "HSBC", "M&T Bank", "Truist", "Regions Bank", "Social Finance" ]
  return f"{random.choice(orgs)}"

def generate_business():
  orgs = ["Amazon", "Alibaba Group", "eBay", "The Home Depot", "Walmart", "MercadoLibre", "Costco", "Flipkart", "Jingdong Mall", "Pinduoduo", "Meta", "Target", "Microsoft", "Apple ", "Samsung", "Craigslist", "Best Buy", "Etsy", "Wish", "Macy’s", "ASOS", "Wildberries", "Coupang", "Wayfair", "Chewy", "Zalando", "IKEA", "Newegg", "Ozon", "Shopee"]
  return f"{random.choice(orgs)}" 

def generate_credit_card():
  # This generates a random number that follows the format of a credit card but is not guaranteed to be valid
  return f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

# Define log levels
log_levels = ["INFO", "WARN", "DEBUG", "ERROR", "PLAIN"]

# Function to generate a single log entry
def generate_log_entry():

  log_level = random.choice(log_levels)

  message = "System reboot requested......."
  if random.random() < 0.80:  # 50% of PII

    # Sample messages for different log levels
    if log_level == "INFO":
      if random.random() < 0.70:  # 70% chance of Payment
        message = f"log.level={log_level}: Payment successful for order #{random.randint(1000, 9999)} (user: {generate_name()}, {generate_email()}). Phone: {generate_phone_number()}, Address: {generate_address()}, Ordered from: {generate_business()}"
      else:
        message = f"log.level={log_level}: User {generate_name()} ({generate_email()}) logged in from {random.randint(100, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}."

    elif log_level == "WARN":
      message = f"log.level={log_level}: Order processing failed for user {generate_name()} ({generate_email()}), credit card: {generate_credit_card()} (invalid CVV) with {generate_org()}"
    elif log_level == "DEBUG":
      message = f"log.level={log_level}: Product update: '{random.choice(['T-Shirt', 'Hat', 'Book'])}' (SKU: ABC{random.randint(100, 999)}) - description changed."
    elif log_level == "ERROR":
      message = f"log.level={log_level}: Database connection timed out (host: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}, user: db_admin)."

  # Additional messages without PII data
  else:
    message_options = [
      f"log.level=INFO: Application started successfully (version 2.1.0).",
      f"log.level=INFO: User session expired.",
      f"log.level=INFO: API request received for resource: /{random.choice(['products', 'users', 'orders'])}.",
      f"log.level=INFO: API request processed successfully (response time: {random.randint(10, 100)}ms).",
      f"log.level=WARN: Low disk space: {random.randint(0, 100)/10.0}% available",
      f"\"POST /opentelemetry.proto.collector.trace.v1.TraceService/Export HTTP/2\" 200 - via_upstream - \"-\" 2483 7 3",
      f"Reader was closed. Closing. Path='/var/log/containers/collector-6d6nt_gmp-system_prometheus-1fa4b153123fce54a8fdb8f12e921fadac9e3785fbc22804ecea02225a8cb915.log"

    ]
    message = f"{random.choice(message_options)}"
  return message

def main():
  num_lines = LOG_NUM_LINES
  with open(LOG_FILE_NAME, 'w') as writefile:

    for _ in range(num_lines):
      log_message = generate_log_entry()
      log_line = f"[{datetime.now(timezone.utc).astimezone().isoformat()+"Z"}] {log_message}"
      #log_line = f"{log_message}"
      #print({log_line})
      writefile.write(log_line+"\n")

  print(f"Wrote {num_lines} log lines")

if __name__ == "__main__":
  main()