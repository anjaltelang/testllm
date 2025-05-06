from typing import List
import requests
import json
import os

from rich.console import Console
from rich.markdown import Markdown

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Tool, Agent


@Tool
def query_deployment_risks(deployment_name: str) -> str:
    """
    Given a deployment name, fetch risks associated with deployment IDs from RHACS.

    Args:
        deployment_name (str): Name (or partial name) of the deployment.
        rhacs_url (str): RHACS Central URL.

    Returns:
        str: Combined JSON string with risks for the given deployment name.
    """
    result = ""
    
    headers = {
        "Authorization": f"Bearer {os.environ['RHACS_API_TOKEN']}",
    }
    search_url = f"{os.environ['RHACS_CENTRAL_URL']}/v1/deployments"
 
    try:
        response = requests.get(search_url, headers=headers, verify=False)
        response.raise_for_status()
        # This will return list of all deployments 
        deployments = response.json().get("deployments", [])
        # Filtering to get ids that match the deployment name
        matching_ids = [
            deployment.get("id")
            for deployment in deployments
            if deployment_name.lower() in deployment.get("name", "").lower()
        ]

        if not matching_ids:
            return f"No deployment found with name matching '{deployment_name}'."
        # Fetch risk for each of the matching ids  
        result = get_risks(matching_ids, headers)
        return result

    except requests.exceptions.RequestException as e:
        return f"Error fetching deployment IDs: {e}"


def get_risks(deployment_ids: List[str], headers: dict) -> str:
    """
    Given a list of deployment IDs, return risks for each one.

    Args:
        deployment_ids (List[str]): List of Deployment IDs.
        headers (dict): Auth headers.

    Returns:
        str: Combined JSON string with risks for all deployments.
    """

    all_risks = {}

    for deployment_id in deployment_ids:
        # Fetch risks for deployment_id from RHACS
        url = f"{os.environ['RHACS_CENTRAL_URL']}/v1/deploymentswithrisk/{deployment_id}"
        print(url)

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()

            deployment_risk = response.json()
            all_risks[deployment_id] = deployment_risk

        except requests.exceptions.RequestException as e:
            all_risks[deployment_id] = f"Error fetching risks: {e}"
    # Convert into json formatted string and return 
    return json.dumps(all_risks, indent=2)


if __name__ == "__main__":
    # Example inputs
    # Step 1: Get User inputs
    deployment_name = input("Enter a deployment name: ")

    # Step 2: Instantiate Model Class
    # Creates a client that talks to Ollama's llama3 model running locally
    ollama_model = OpenAIModel(
        model_name="llama3.2",
        provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
    )
    # Step 3: Instantiate Agent that has access to query_deployment_risk tool
    # query_deployment_risk tool calls the ACS API to get risks
    acs_agent = Agent(
        ollama_model,
        system_prompt="You are a support agent familiar with RHACS features. Respond to the user queries.",
        tools=[query_deployment_risks],
    )
    # Step 4: Run the agent
    result = acs_agent.run_sync(
        f"""
        Identify and summarize all risks related to {deployment_name} deployment \
in Red Hat Advanced Cluster Security (RHACS). Additionally, provide recommended \
remediation steps for each identified risk.
        """,
    )

    console = Console()    
    console.print(result.output)    
    # print("*" * 25)
    # print(result.output)
    # print("*" * 25)
