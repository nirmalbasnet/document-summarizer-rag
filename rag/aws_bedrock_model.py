import os
import boto3
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

def get_client():
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
    AWS_REGION = os.getenv('AWS_REGION')

    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
    )

    return bedrock_client

def get_model():
    AWS_REGION = os.getenv('AWS_REGION')

    bedrock_client = get_client()

    model = ChatBedrock(
        client=bedrock_client,
        model_id="amazon.nova-lite-v1:0",
        region_name=AWS_REGION,
        temperature=0
    )

    return model

def get_embeddings_model():
    bedrock_client = get_client()
    embeddings = BedrockEmbeddings(
        client=bedrock_client,
        model_id="amazon.titan-embed-text-v2:0",
    )

    return embeddings