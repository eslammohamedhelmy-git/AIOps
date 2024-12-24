
import subprocess
import time
import requests
import xml.etree.ElementTree as ET
import re
import openai
from itertools import islice
import os
from os import listdir
import glob
import requests
## email libraries
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv('/Users/Islam.mohamed5/Desktop/.env')

# Static variables
JENKINS_URL = "http://10.236.38.121:32000"  # Jenkins URL
JOB_NAME = "AIOps"  # Jenkins job name
USERNAME = os.getenv("JENKINS_USERNAME") # Jenkins username
API_TOKEN = os.getenv("API_TOKEN_JENKINS") # Jenkins API token
BACKUP_DIRECTORY = "/Users/Islam.mohamed5/Desktop/hackathon"  # Directory to store backups
BUILD_POLL_INTERVAL = 10  # Time in seconds between status checks


def auditing(jenkins_url,job_name,build_number,FLAG):
    # # send email to Teams Channel, Auditing
    webhook_url = "https://vodafone.webhook.office.com/webhookb2/eb0c06d1-590f-4bac-b21d-fd6a41e86cde@68283f3b-8487-4c86-adb3-a5228f18b893/IncomingWebhook/471c53e15e7d4ddb9fc6fdc5eb0c6001/8073a3a4-4a6a-4909-bacf-f7eff6c2fcc4"
    content = f"Build Fixed Using AI with Build URL: {jenkins_url}/job/{job_name}/{build_number}/ :large_green_circle: :large_green_circle:"
    if not FLAG :
        content =  f"Build Failed Using AI with Build URL: {jenkins_url}/job/{job_name}/{build_number}/ :large_red_circle: :large_red_circle:"
    message = {
    "text": content
    }
    response = requests.post(webhook_url, json=message)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
    # send email to Islam vodafone email from alaaamr1995@gmail.com
    sender_email = os.getenv("SENDER_EMAIL",None)
    password = os.getenv("APP_PASSWORD",None)
    smtp_server_url= os.getenv("SMTP_SERVER","smtp.gmail.com")

    receiver_email = "islam.mohamed5@vodafone.com"
    subject = "Ai Report - Fixed CI/CD with AI"
    html_body = "Build updated  <a href= '{jenkins_url}/job/{job_name}/{build_number}/'> click here </a>"

    # Create a multipart message and set headers
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(html_body, "html"))


    # Start SSL (secure socket layer) connection
    with smtplib.SMTP_SSL(smtp_server_url, 465) as smtp_server:
            # Login to the SMTP server using the sender's credentials.
            smtp_server.login(sender_email, password)
            smtp_server.sendmail(sender_email, [receiver_email], message.as_string())
    print("Email sent successfully")



def get_jenkins_crumb(jenkins_url, username, api_token):
    try:
        response = requests.get(f"{jenkins_url}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)", auth=(username, api_token))
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"Failed to obtain Jenkins crumb: {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error obtaining Jenkins crumb: {e}")
        return None

def trigger_jenkins_build(jenkins_url, job_name, username, api_token):
    crumb = get_jenkins_crumb(jenkins_url, username, api_token)
    if crumb is None:
        print("Failed to obtain Jenkins crumb. Exiting.")
        return False, None

    headers = {
        crumb.split(':')[0]: crumb.split(':')[1]
    }
    try:
        response = requests.post(f"{jenkins_url}/job/{job_name}/build", auth=(username, api_token), headers=headers)
        if response.status_code == 201:
            print("Build triggered successfully")
            queue_location = response.headers.get('Location')
            if queue_location:
                queue_item_number = queue_location.split('/')[-2]
                build_number = wait_for_build_to_start(jenkins_url, job_name, queue_item_number, username, api_token)
                return True, build_number
            else:
                print("Failed to retrieve queue location.")
                return False, None
        else:
            print(f"Failed to trigger build: {response.text}")
            return False, None
    except requests.RequestException as e:
        print(f"Error triggering Jenkins build: {e}")
        return False, None

 
    
def extract_jenkinsfile_from_config(config_xml_path, output_file_path):
    if not os.path.exists(config_xml_path):
        print(f"Error: The file {config_xml_path} does not exist.")
        return

    try:
        # Parse the XML file
        tree = ET.parse(config_xml_path)
        root = tree.getroot()
        
        # Find the Jenkinsfile script
        script_element = root.find(".//script")
        if script_element is not None:
            jenkinsfile_content = script_element.text
            
            # Save the Jenkinsfile content to the specified output file
            with open(output_file_path, 'w') as file:
                file.write(jenkinsfile_content)
            print(f"Jenkinsfile extracted and saved to {output_file_path}")
        else:
            print("No Jenkinsfile script found in the config.xml")
    except ET.ParseError as e:
        print(f"Error parsing the config.xml: {e}")

# Example usage
#config_xml_path = "/Users/abdelaatyh2/Downloads/hackathon/h/config.xml"
output_file_path = "/Users/Islam.mohamed5/Desktop/hackathon/WrongJenkinsfile"
def wait_for_build_to_start(jenkins_url, job_name, queue_item_number, username, api_token):
    try:
        while True:
            response = requests.get(f"{jenkins_url}/queue/item/{queue_item_number}/api/xml", auth=(username, api_token))
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                executable = root.find('executable')
                if executable is not None:
                    build_number = executable.find('number').text
                    return build_number
            time.sleep(BUILD_POLL_INTERVAL)
    except Exception as e:
        print(f"Error while waiting for build to start: {e}")
    return None

def upload_and_trigger_local_jenkinsfile(jenkins_url, local_jenkinsfile_path, job_name, username, api_token):
    crumb = get_jenkins_crumb(jenkins_url, username, api_token)
    if crumb is None:
        print("Failed to obtain Jenkins crumb. Exiting.")
        return False
# put the correct jenkins file here(local_jenkinsfile_path)
    try:
        with open('/Users/Islam.mohamed5/Desktop/hackathon/WrongJenkinsfile', 'r') as f:
          jenkinsfile_content1 = f.read()
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        result = openai.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = [
                {
                    "role": "user",
                    "content":  "give me correct jenkins file for this" +  jenkinsfile_content1
                    }
            ]
        )
        def extract_groovy_code(output3):
                pattern1 = r'```groovy(.*?)```'
                match = re.search(pattern1, output3, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return None
        output3= result.choices[0].message.content
        groovy_code = extract_groovy_code(output3)
        if groovy_code:
            with open('Jenkinsfile', 'w') as file:
                file.write(groovy_code)
            print("Groovy code extracted and saved to Jenkinsfile.")
        else:
            with open('Jenkinsfile', 'w') as file:
                file.write(output3)
            print("No groovy code block found.")
        with open('/Users/Islam.mohamed5/Desktop/hackathon/Jenkinsfile', 'r') as f:
            jenkinsfile_content = f.read()

        config_xml = f"""
<flow-definition plugin="workflow-job@2.39">
  <description>Fallback job</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.80">
    <script>{jenkinsfile_content}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
        """
        headers = {
            crumb.split(':')[0]: crumb.split(':')[1],
            'Content-Type': 'application/xml'
        }
        response = requests.post(f"{jenkins_url}/job/{job_name}/config.xml", auth=(username, api_token), headers=headers, data=config_xml)
        if response.status_code == 200:
            print(f"Job {job_name} updated successfully with fallback Jenkinsfile")
            return True
        else:
            print(f"Failed to update job: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error updating Jenkins job: {e}")
        return False
    # Specify the directory
    directory = "/Users/Islam.mohamed5/Desktop/hackathon"
    # Loop through all files in the directory
    for filename in os.listdir(directory):
        # Construct full file path
        file_path = os.path.join(directory, filename)
        # Check if it is a file (not a directory)
        if os.path.isfile(file_path):
            # Check if the filename contains a dot
            if '.' in filename:
                # Split the filename and check the extension
                extension = filename.split('.')[-1].lower()
                # If the extension is not 'py', remove the file
                if extension != 'py':
                    os.remove(file_path)
                    print(f"Removed {file_path}")
            else:
                # If there is no dot, it means there's no extension, remove the file
                os.remove(file_path)
                print(f"Removed {file_path}")
    
    
def save_initial_job_config(jenkins_url, job_name, username, api_token, build_number):
    crumb = get_jenkins_crumb(jenkins_url, username, api_token)
    if crumb is None:
        print("Failed to obtain Jenkins crumb. Exiting.")
        return False

    try:
        headers = {
            crumb.split(':')[0]: crumb.split(':')[1]
        }
        response = requests.get(f"{jenkins_url}/job/{job_name}/config.xml", auth=(username, api_token), headers=headers)
        if response.status_code == 200:
            initial_config_path = f"{BACKUP_DIRECTORY}/initial_config_{job_name}_build_{build_number}.xml"
            with open(initial_config_path, 'w') as f:
                f.write(response.text)
            print(f"Initial job config saved to {initial_config_path}")
            extract_jenkinsfile_from_config(initial_config_path, output_file_path)
            return initial_config_path
        else:
            print(f"Failed to get initial job config: {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error getting initial job config: {e}")
        return None

def get_build_console_log(jenkins_url, job_name, build_number, username, api_token):
    try:
        response = requests.get(f"{jenkins_url}/job/{job_name}/{build_number}/consoleText", auth=(username, api_token))
        if response.status_code == 200:
            log_path = f"{BACKUP_DIRECTORY}/build_{job_name}_console_log_{build_number}.txt"
            with open(log_path, 'w') as f:
                f.write(response.text)
            print(f"Console log for build {build_number} saved to {log_path}")
            return log_path
        else:
            print(f"Failed to get console log: {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error getting console log: {e}")
        return None

def restore_initial_job_config(jenkins_url, job_name, username, api_token, initial_config_path):
    crumb = get_jenkins_crumb(jenkins_url, username, api_token)
    if crumb is None:
        print("Failed to obtain Jenkins crumb. Exiting.")
        return False

    try:
        with open(initial_config_path, 'r') as f:
            initial_config_content = f.read()

        headers = {
            crumb.split(':')[0]: crumb.split(':')[1],
            'Content-Type': 'application/xml'
        }
        response = requests.post(f"{jenkins_url}/job/{job_name}/config.xml", auth=(username, api_token), headers=headers, data=initial_config_content)
        if response.status_code == 200:
            print("Initial job config restored successfully.")
            return True
        else:
            print(f"Failed to restore initial job config: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error restoring initial job config: {e}")
        return False

def main():
    success, initial_build_number = trigger_jenkins_build(JENKINS_URL, JOB_NAME, USERNAME, API_TOKEN)
    if success:
        print(f"Build {initial_build_number} triggered successfully")
        print(f"Waiting for Jenkins job '{JOB_NAME}' build {initial_build_number} to finish...")
        initial_config_path = save_initial_job_config(JENKINS_URL, JOB_NAME, USERNAME, API_TOKEN, initial_build_number)

        if initial_config_path is None:
            print("Failed to save initial job config. Exiting.")
            return

        time.sleep(BUILD_POLL_INTERVAL)
        response = requests.get(f"{JENKINS_URL}/job/{JOB_NAME}/{initial_build_number}/api/xml", auth=(USERNAME, API_TOKEN))
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            result = root.find('result')
            
            # Save the console log for the initial build regardless of the result
            get_build_console_log(JENKINS_URL, JOB_NAME, initial_build_number, USERNAME, API_TOKEN)
            
            if result is not None and result.text == "FAILURE":
                print(f"Initial build {initial_build_number} failed. Triggering fallback Jenkinsfile...")
                for i in range(1):
                    print(f"Attempt {i+1} to trigger fallback Jenkinsfile")
                    #LOCAL_JENKINSFILE_PATH = input("Enter the path to the local Jenkinsfile: ")
                    if upload_and_trigger_local_jenkinsfile(JENKINS_URL,'/Users/Islam.mohamed5/Desktop/hackathon/jenkins_file', JOB_NAME, USERNAME, API_TOKEN):
                        success, fallback_build_number = trigger_jenkins_build(JENKINS_URL, JOB_NAME, USERNAME, API_TOKEN)
                        if success:
                            print(f"Fallback build {fallback_build_number} triggered successfully. Waiting for it to finish...")
                            time.sleep(BUILD_POLL_INTERVAL)
                            response = requests.get(f"{JENKINS_URL}/job/{JOB_NAME}/{fallback_build_number}/api/xml", auth=(USERNAME, API_TOKEN))
                            if response.status_code == 200:
                                root = ET.fromstring(response.content)
                                result = root.find('result')
                                if result is not None and result.text == "SUCCESS":
                                    print(f"Fallback build {fallback_build_number} succeeded.")
                                    # Save the console log for the fallback build
                                    get_build_console_log(JENKINS_URL, JOB_NAME, fallback_build_number, USERNAME, API_TOKEN)
                                    auditing(JENKINS_URL,JOB_NAME,fallback_build_number,True)
                                    return
                                else:
                                    print(f"Fallback build {fallback_build_number} failed.")
                                    auditing(JENKINS_URL,JOB_NAME,fallback_build_number,False)
                                    # jenkins job failed
                            else:
                                print(f"Failed to retrieve build status for fallback build {fallback_build_number}.")
                                # jenkins request issue{404}
                        else:
                            print("Failed to trigger fallback Jenkins build.")
                            #jenkins file cannot be applied
                    else:
                        print("Failed to update job with fallback Jenkinsfile.")
                      # issue in upload_and_trigger_local_jenkinsfile function.
                print("All fallback attempts failed. Restoring initial job config...")
                if restore_initial_job_config(JENKINS_URL, JOB_NAME, USERNAME, API_TOKEN, initial_config_path):
                                        pattern = r"(?i)(error|notfound|ERROR|Error)"  # Case-insensitive pattern to search for "error", "ERROR", or "NotFound"
                                        # Open and read each line of a file
                                        directory_path = "/Users/Islam.mohamed5/Desktop/hackathon"
                                        txt_files = glob.glob(os.path.join(directory_path, "*.txt"))
                                        for txt_file in txt_files:
                                            with open(txt_file, "r") as file:
                                                lines = file.readlines() 
                                                output = ""
                                                for index, line in enumerate(lines): 
                                                    if re.search(pattern, line):
                                                            start_index = max(0, index - 5)
                                                            end_index = min(len(lines), index + 5)
                                                            output += "".join(lines[start_index:end_index]) + "\n"
                                        load_dotenv()
                                        openai.api_key = os.getenv("OPENAI_API_KEY")
                                        result = openai.chat.completions.create(
                                            model = "gpt-3.5-turbo",
                                            messages = [
                                                {
                                                    "role": "user",
                                                    "content":  output 
                                                    }
                                            ]
                                        )
                                        print("Initial job config restored successfully.")
                                        print("The solution for this Error is")    
                                        print(result.choices[0].message.content)                  
                else:
                    print("Failed to restore initial job config.")
            else:
                print(f"Initial build {initial_build_number} succeeded.")
        else:
            print(f"Failed to retrieve build status for initial build {initial_build_number}.")
    else:
        print("Failed to trigger initial Jenkins build.")

# Specify the directory
directory = "/Users/Islam.mohamed5/Desktop/hackathon"
# Loop through all files in the directory
for filename in os.listdir(directory):
    # Construct full file path
    file_path = os.path.join(directory, filename)
    # Check if it is a file (not a directory)
    if os.path.isfile(file_path):
        # Check if the filename contains a dot
        if '.' in filename:
            # Split the filename and check the extension
            extension = filename.split('.')[-1].lower()
            # If the extension is not 'py', remove the file
            if extension != 'py':
                os.remove(file_path)
                print(f"Removed {file_path}")
        else:
            # If there is no dot, it means there's no extension, remove the file
            os.remove(file_path)
            print(f"Removed {file_path}")

if __name__ == "__main__":
    main()

