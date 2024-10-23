import itertools
import boto3
import botocore
import chromadb
import math
import json
import os
from chromadb.utils.embedding_functions import amazon_bedrock_embedding_function


MAX_MESSAGES = 20


class ChatMessage:
    def __init__(self, role, text):
        self.role = role
        self.text = text

    def __str__(self):
        return f"**Role:** {self.role}\n**Text:** {self.text}"


def get_collection(path, collection_name):
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
    )
    embedding_function = (
        amazon_bedrock_embedding_function.AmazonBedrockEmbeddingFunction(
            session=session, model_name="amazon.titan-embed-text-v2:0"
        )
    )

    client = chromadb.PersistentClient(path=path)
    print("Connected to chromadb")
    print("Listing collections:")
    print(client.list_collections())
    collection = client.get_collection(
        collection_name, embedding_function=embedding_function
    )

    return collection


def get_vector_search_results(collection, question):
    results = collection.query(query_texts=[question], n_results=4)

    return results


def get_tools():
    tools = [
        {
            "toolSpec": {
                "name": "get_amazon_bedrock_information",
                "description": "Retrieve information about Amazon Bedrock, a managed service for hosting generative AI models.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The retrieval-augmented generation query used to look up information in a repository of FAQs about Amazon Bedrock.",
                            }
                        },
                        "required": ["query"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "cosine",
                "description": "Calculate the cosine of x.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "x": {
                                "type": "number",
                                "description": "The number to pass to the function.",
                            }
                        },
                        "required": ["x"],
                    }
                },
            }
        },
    ]

    return tools


# allow to send a list of current and past messages to Amazon Bedrock for processing.
def convert_chat_messages_to_converse_api(chat_messages):
    print("---> starting convert_chat_messages_to_converse_api...")
    messages = []

    for chat_msg in chat_messages:
        # If chat_msg is a dict, assume it's already formatted for Bedrock API
        if isinstance(chat_msg, dict):
            messages.append(chat_msg)
        else:
            print("---> it's a ChatMessage object, format it for the Bedrock API")
            print(chat_msg)
            messages.append(
                {"role": chat_msg.role, "content": [{"text": chat_msg.text}]}
            )

    return messages


# function to handle any tool use requests.
# checks the model's response to see if the get_amazon_bedrock_information tool was requested
# if it was, retrieves relevant content from the vector database
# and submit an additional request to Anthropic Claude to generate a final response based on the retrieved content.
def process_tool(response_message, messages, bedrock, tool_list):
    print("[rag_lib] --> Starting process_tool()")
    messages.append(response_message)

    response_content_blocks = response_message["content"]
    follow_up_content_blocks = []
    is_rag_used = False
    tool_used = None
    for content_block in response_content_blocks:
        if "toolUse" in content_block:
            tool_use_block = content_block["toolUse"]

            tool_used = tool_use_block["name"]
            if (tool_use_block["name"]) == "get_amazon_bedrock_information":
                print("Using tool: get_amazon_bedrock_information!")
                is_rag_used = True

                collection = get_collection("./data/chroma", "bedrock_faqs_collection")

                query = tool_use_block["input"]["query"]

                print("---QUERY---")
                print(query)

                search_results = get_vector_search_results(collection, query)
                flattened_results_list = list(
                    itertools.chain(*search_results["documents"])
                )  # flatten the list of lists returned by chromadb

                rag_content = "\n\n".join(flattened_results_list)

                print("---RAG CONTENT---")
                print(rag_content)

                follow_up_content_blocks.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_block["toolUseId"],
                            "content": [{"text": rag_content}],
                        }
                    }
                )
            elif (tool_use_block["name"]) == "cosine":
                print("Using tool: cosine!")
                is_rag_used = True
                tool_result_value = math.cos(tool_use_block["input"]["x"])
                follow_up_content_blocks.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_block["toolUseId"],
                            "content": [{"json": {"result": tool_result_value}}],
                        }
                    }
                )

    if len(follow_up_content_blocks) > 0:
        follow_up_message = {"role": "user", "content": follow_up_content_blocks}

        messages.append(follow_up_message)

        response = bedrock.converse(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=messages,
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0,
                "topP": 0.9,
                "stopSequences": [],
            },
            toolConfig={"tools": tool_list},
        )
        print("---- BEDROCK RESPONSE ----")
        print(json.dumps(response, indent=4))
        response_output = response["output"]["message"]["content"][0]["text"]
        if is_rag_used:
            response_output = (
                "[RAG] - Tool Config: " + tool_used + "\n\n" + response_output
            )

        return True, response_output  # tool used, response
    else:
        return False, None  # tool not used,


# function to handle the request from the Streamlit front end application.
# creates an Amazon Bedrock client with Boto3, then passes the input content to Amazon Bedrock.
# It can then optionally handle a tool use request if necessary.
def chat_with_model(message_history, new_text=None):
    try:
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
        )
        bedrock = session.client(service_name="bedrock-runtime")
        print("[rag_lib] --> Starting chat_with_model")
        print("bedrock-->" + str(bedrock))
        tool_list = get_tools()

        if new_text:
            print("[rag_lib] --> new text...")
            new_text_message = ChatMessage("user", text=new_text)
            print("[rag_lib] --> new_text_message " + new_text_message.__str__())
            message_history.append(new_text_message)

        number_of_messages = len(message_history)
        print("[rag_lib] --> number of messages: " + str(number_of_messages))

        if number_of_messages > MAX_MESSAGES:
            del message_history[0 : (number_of_messages - MAX_MESSAGES) * 2]

        messages = convert_chat_messages_to_converse_api(message_history)

        print("---> Prepared messages ot bedrock...")
        print(messages)
        response = bedrock.converse(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            messages=messages,
            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0,
                "topP": 0.9,
                "stopSequences": [],
            },
            toolConfig={"tools": tool_list},
        )

        response_message = response["output"]["message"]
        tool_used, output = process_tool(response_message, messages, bedrock, tool_list)

        if not tool_used:
            print("[rag_lib] --> NOT TOOL USED!")
            output = response["output"]["message"]["content"][0]["text"]

        print("[rag_lib] ---> FINAL RESPONSE ---")
        print("[rag_lib] output:" + output)

        return output

    except botocore.exceptions.ParamValidationError as e:
        print(f"[rag_lib] Parameter validation error: {str(e)}")
        return f"[rag_lib] An error occurred: {str(e)}"
    except botocore.exceptions.ClientError as e:
        print(f"[rag_lib] AWS client error: {str(e)}")
        return f"[rag_lib] An error occurred: {str(e)}"
    except Exception as e:
        print(f"[rag_lib] An unexpected error occurred: {str(e)}")
        return f"[rag_lib] An unexpected error occurred: {str(e)}"
