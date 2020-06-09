import datetime
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import cv2
import numpy as np
import sys
from ibm_watson import VisualRecognitionV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import ibmiotf.application
import ibmiotf.device
import random
import time
import json
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey



#Provide your IBM Watson Device Credentials
organization = "x865gr"
deviceType = "rsip"
deviceId = "1001"
authMethod = "token"
authToken = "1234567890"

authenticator = IAMAuthenticator('uzbettbRqM8UJMbtvIeoo7YgWa8RtvMx6Gf0NwpiHC6h')
visual_recognition = VisualRecognitionV3(
    version='2018-03-19',
    authenticator=authenticator
)

visual_recognition.set_service_url('https://api.us-south.visual-recognition.watson.cloud.ibm.com/instances/c63250f3-2cef-47f8-b893-482f5475b713')


##def myCommandCallback(cmd):
##        print("Command received: %s" % cmd.data)
##        print(cmd.data['command'])
##
##        if(cmd.data['command']=="open"):
##                print("door open")
##
##        if(cmd.data['command']=="close"):
##                print("door close")
##

try:
	deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
	deviceCli = ibmiotf.device.Client(deviceOptions)
	#..............................................

except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()

# Connect and send a datapoint "hello" with value "world" into the cloud as an event of type "greeting" 10 times
#deviceCli.connect()


#It will read the first frame/image of the video
video=cv2.VideoCapture(0)
print("videoooo")




COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "zvX7TxWyLk-tjhH6SM1YGLqUVv_nbUDvtxYA7F_qDGQs" # eg "W00YiRnLW4a3fTjMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/a0a6e53707df41969e9420072953f316:a940ce0b-ef90-4c36-b8f7-f1f6b6bcb09b::"
picname="sample2.jpg"
client = Cloudant("ea565ab2-700a-4181-b79d-ceeb00531bb1-bluemix", "3d20a995e83a0d24f4226afd6dfc6dcff2164191283ab002b3388a89e8255b81", url="https://ea565ab2-700a-4181-b79d-ceeb00531bb1-bluemix:3d20a995e83a0d24f4226afd6dfc6dcff2164191283ab002b3388a89e8255b81@ea565ab2-700a-4181-b79d-ceeb00531bb1-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()
database_name = "doorbell"

# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)


def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))



while True:
        #capture the first frame
        check,frame=video.read()
        cv2.imshow('Video Streaming', frame)
        picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
        picname=picname+".jpg"
       
        pic=picname
        cv2.imwrite(picname,frame)
        
        picname="sam2.jpeg"
        with open(picname,'rb') as images_file:
            classes = visual_recognition.classify(
                images_file=images_file,
                threshold='0.6').get_result()
            print(json.dumps(classes, indent=2))
            for i in classes['images'][0]['classifiers'][0]['classes']:
                if i['class']=='car':
                    print("car is detected")
                    person=1
                    my_database = client.create_database(database_name)
                    multi_part_upload("cloud-object-storage-dsx-cos-standard-s33",picname,picname)
                    if my_database.exists():
                        print("'{database_name}' successfully created.")
                        json_document = {
                            "_id": pic,
                            "link":COS_ENDPOINT+"/cloud-object-storage-dsx-cos-standard-s33/"+picname
                            }
                        new_document = my_database.create_document(json_document)
                        if new_document.exists():
                            print("Document '{new_document}' successfully created.")
                        
            time.sleep(1)
            t=34
            h=45
        data = {"d":{ 'temperature' : t, 'humidity': h, 'person': person}}
        #print data
##        def myOnPublishCallback():
##            print ("Published data to IBM Watson")
##
##        success = deviceCli.publishEvent("Data", "json", data, qos=0, on_publish=myOnPublishCallback)
##        if not success:
##            print("Not connected to IoTF")
##        time.sleep(1)
##        deviceCli.commandCallback = myCommandCallback
        person=0
    #waitKey(1)- for every 1 millisecond new frame will be captured
        Key=cv2.waitKey(1)
        if Key==ord('q'):
        #release the camera
            video.release()
        #destroy all windows
            cv2.destroyAllWindows()
            break
##deviceCli.disconnect()
            
