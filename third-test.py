from typing import List
import requests
import json

from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Tool, Agent




@Tool
def query_deployment_risks(
    deployment_name: str,
    rhacs_url: str,
    api_token: str
) -> str:
    """
    Given a deployment name, fetch risks associated with deployment IDs from RHACS.

    Args:
        deployment_name (str): Name (or partial name) of the deployment.
        rhacs_url (str): RHACS Central URL.
        api_token (str): RHACS API token.

    Returns:
        str: Combined JSON string with risks for all deployments.
    """
    result = ''
    headers = {
    "Authorization": f"Bearer {api_token}",
    }
    search_url = f"{rhacs_url}/v1/deployments"


    try:
        response = requests.get(search_url, headers=headers, verify=False)
        response.raise_for_status()
        deployments = response.json().get("deployments", [])

        matching_ids = [
            deployment.get("id")
            for deployment in deployments
            if deployment_name.lower() in deployment.get("name", "").lower()
        ]

        if not matching_ids:
            return f"No deployment found with name matching '{deployment_name}'."

        result = get_risks(matching_ids, rhacs_url, headers)
        return result

    except requests.exceptions.RequestException as e:
        return f"Error fetching deployment IDs: {e}"


def get_risks(deployment_ids: List[str], rhacs_url: str, headers: dict) -> str:
    """
    Given a list of deployment IDs, return risks for each one.

    Args:
        deployment_ids (List[str]): List of Deployment IDs.
        rhacs_url (str): RHACS Central URL.
        headers (dict): Auth headers.

    Returns:
        str: Combined JSON string with risks for all deployments.
    """

    all_risks = {}

    for deployment_id in deployment_ids:
        if "Error" in deployment_id or "No deployment" in deployment_id:
            continue

        url = f"{rhacs_url}/v1/deploymentswithrisk/{deployment_id}"

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()

            deployment_risk = response.json()
            all_risks[deployment_id] = deployment_risk

        except requests.exceptions.RequestException as e:
            all_risks[deployment_id] = f"Error fetching risks: {e}"

    return json.dumps(all_risks, indent=2)


if __name__ == "__main__":
    # Example inputs
    RHACS_CENTRAL_URL = input("Enter RHACS Central URL: ").strip()
    API_TOKEN = input("Enter RHACS API Token: ").strip()

    ollama_model = OpenAIModel(
        model_name="llama3.2",
        provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
    )

    acs_agent = Agent(
        ollama_model,
        system_prompt="You are a support agent familiar with RHACS features. Respond to the user queries.",
        tools=[query_deployment_risks],
    )

    result = acs_agent.run_sync(
        f"""
        Summarize all risks associated with 'cert-manager-operator-controller-manager' deployment in RHACS.
        Use this URL: {RHACS_CENTRAL_URL} and token: {API_TOKEN}
        Suggest remediations for the risks.
        """,
    )

    print(result.output)
