From langchain_aws import ChatBedrockConverse, BedrockEmbeddings
import pymysql
import json
import boto3


def load_aws():
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="ap-northeast-2",
        endpoint_url="https://vpce-095df641fa2ee614e-vzbvefgu.bedrock-runtime.ap-northeast-2.vpce.amazonaws.com"
    )
    llm = ChatBedrockConverse(model="apac.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name='ap-northeast-2',
        client=bedrock_client)

    return llm

def load_embedding_model():

    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="ap-northeast-2",
        endpoint_url="https://vpce-095df641fa2ee614e-vzbvefgu.bedrock-runtime.ap-northeast-2.vpce.amazonaws.com"
    )
    embeddings = BedrockEmbeddings(
        region_name='ap-northeast-2',
        model_id = "amazon.titan-embed-text-v2:0",
        client=bedrock_client)
    import pdb
    pdb.set_trace()
    return embeddings