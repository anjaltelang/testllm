from typing import List
import requests
import json

from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Tool, Agent

# RHACS constants
RHACS_CENTRAL_URL = "https://central-stackrox.apps.cluster-vnks4.vnks4.sandbox430.opentlc.com"
API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imp3dGswIiwidHlwIjoiSldUIn0.eyJFeHBpcmVBdCI6IjIwMjUtMDQtMjhUMDQ6MDA6MDBaIiwiYXVkIjoiaHR0cHM6Ly9zdGFja3JveC5pby9qd3Qtc291cmNlcyNhcGktdG9rZW5zIiwiZXhwIjoxNzQ1ODEyODAwLCJpYXQiOjE3NDU3MjAzMDYsImlzcyI6Imh0dHBzOi8vc3RhY2tyb3guaW8vand0IiwianRpIjoiYjYwNTM4ZjctZDFkYi00ZWYxLWI2YWMtMTcyZGI4ZDg0NjU2IiwibmFtZSI6InRlc3QiLCJyb2xlcyI6WyJBZG1pbiJdfQ.pf8jJvYuW_9d9IUYoqgL4s16qIXqcl-GKhE_lYUKu5G5VwIHz6WKPGh44cKvZNdRQX80KRI1I__mkFKXTXVNd2cNvdM3Z9CYewLs-fwesSHv0iDyBr62pIj9szNiilQbkJWBmKd-NfA0sRhuzBBx_ugj5aF1PtytDSSR7mn-pplUunKTpmhZj-LRAp7BO8nWM3vyb7Chduobm8hDZpHOssoVSE0azacqPDaoDLHgWr026d3aRt-dX5U2NIrdI4aGQ5RXTpr3_4eNyxcnWJkCikWzM_wFFoOTXZRz-epkF2jsOCXBkf3DRf3crScMvYS1zDzMDbA_pe8wizl65GoyhqnGHRFlpjPbbO6pR8SNAoUerV88PtGKYL6F-sjeyk-r3hW-OrXL6oamjHFXJ4fELf01Au7dWY56H21rOtO7rvXC0zJNh3KZihQB7Qt01lYhx3oC-3sOhbfjQ8FY3Vr-SZtyrqC5rUUCu0w9jupoczp5Ucg0ckE8ADoVk66RjVgZaAK8p0b-put9ucbJ4XH4lIyBGUCRx8enscwySDTela5rZDsl_ZRE5lI2cWWzqHvgLjJ0GbHaT5YKvQiwIvjFBmHTjdpmEVxGi3AImIaC2qfoMaDRcnIX3fFjaKUOwglarIgLiF9mT_jtfp_wMachlWbhQyBOth19nelTOMfpv2U"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
}


@Tool
def query_deployment_risks(deployment_name: str) -> str:
    """
    Given a deployment name, fetch risks associated with deployment IDs from RHACS.

    Args:
        deployment_name (str): Name (or partial name) of the deployment.

    Returns:
        str: Combined JSON string with risks for all deployments
    """
    result = ''
    search_url = f"{RHACS_CENTRAL_URL}/v1/deployments"

    try:
        response = requests.get(search_url, headers=HEADERS, verify=False)
        response.raise_for_status()
        deployments = response.json().get("deployments", [])

        # Find matching deployments (case insensitive contains)
        matching_ids = [
            deployment.get("id")
            for deployment in deployments
            if deployment_name.lower() in deployment.get("name", "").lower()
        ]

        if not matching_ids:
            return [f"No deployment found with name matching '{deployment_name}'."]
        
        print("matching ids are:", matching_ids)
        result = get_risks(matching_ids)
        return result

    except requests.exceptions.RequestException as e:
        return [f"Error fetching deployment IDs: {e}"]



def get_risks(deployment_ids: List[str]) -> str:
    """
    Given a list of deployment IDs, return risks for each one.

    Args:
        deployment_ids (List[str]): List of Deployment IDs.

    Returns:
        str: Combined JSON string with risks for all deployments.
    """

    all_risks = {}

    for deployment_id in deployment_ids:
        print("calling get risks for ID : ",deployment_id)
        # Skip error messages in list
        if "Error" in deployment_id or "No deployment" in deployment_id:
            continue

        url = f"{RHACS_CENTRAL_URL}/v1/deploymentswithrisk/{deployment_id}"

        try:
            response = requests.get(url, headers=HEADERS, verify=False)
            response.raise_for_status()

            deployment_risk = response.json()
            print(json.dumps(deployment_risk,indent=2))
            all_risks[deployment_id] = deployment_risk

        except requests.exceptions.RequestException as e:
            all_risks[deployment_id] = f"Error fetching risks: {e}"

    return json.dumps(all_risks, indent=2)


if __name__ == "__main__":
    ollama_model = OpenAIModel(
        model_name="llama3.2",
        provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
    )

    acs_agent = Agent(
        ollama_model,
        system_prompt=(
            "You are a support agent familiar with RHACS features. Respond to the user queries."
        ),
        tools=[query_deployment_risks],
    )

    result = acs_agent.run_sync(
        """
        Summarize all risks associated with 'cert-manager-operator-controller-manager' deployment in rhacs. Suggest remediations for the risks.
        """
    )

    print(result.output)
