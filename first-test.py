from typing import List
import requests
import json

from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Tool, Agent


@Tool
def query_deployment_risks() -> str:
    """
    Returns deployment risks for in RHACS cluster for cert-manager

    Return:
        JSON containing risk information
    """

    # RHACS Central URL and API Endpoint
    RHACS_CENTRAL_URL = (
        "https://central-stackrox.apps.cluster-vnks4.vnks4.sandbox430.opentlc.com"  # Replace with your Central address
    )
    API_ENDPOINT = "/v1/deploymentswithrisk"

    # Authentication: API Token
    API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imp3dGswIiwidHlwIjoiSldUIn0.eyJFeHpcmVBdCI6IjIwMjUtMDQtMjhUMDQ6MDA6MDBaIiwiYXVkIjoiaHR0cHM6Ly9zdGFja3JveC5pby9qd3Qtc291cmNlcyNhcGktdG9rZW5zIiwiZXhwIjoxNzQ1ODEyODAwLCJpYXQiOjE3NDU3MjAzMDYsImlzcyI6Imh0dHBzOi8vc3RhY2tyb3guaW8vand0IiwianRpIjoiYjYwNTM4ZjctZDFkYi00ZWYxLWI2YWMtMTcyZGI4ZDg0NjU2IiwibmFtZSI6InRlc3QiLCJyb2xlcyI6WyJBZG1pbiJdfQ.pf8jJvYuW_9d9IUYoqgL4s16qIXqcl-GKhE_lYUKu5G5VwIHz6WKPGh44cKvZNdRQX80KRI1I__mkFKXTXVNd2cNvdM3Z9CYewLs-fwesSHv0iDyBr62pIj9szNiilQbkJWBmKd-NfA0sRhuzBBx_ugj5aF1PtytDSSR7mn-pplUunKTpmhZj-LRAp7BO8nWM3vyb7Chduobm8hDZpHOssoVSE0azacqPDaoDLHgWr026d3aRt-dX5U2NIrdI4aGQ5RXTpr3_4eNyxcnWJkCikWzM_wFFoOTXZRz-epkF2jsOCXBkf3DRf3crScMvYS1zDzMDbA_pe8wizl65GoyhqnGHRFlpjPbbO6pR8SNAoUerV88PtGKYL6F-sjeyk-r3hW-OrXL6oamjHFXJ4fELf01Au7dWY56H21rOtO7rvXC0zJNh3KZihQB7Qt01lYhx3oC-3sOhbfjQ8FY3Vr-SZtyrqC5rUUCu0w9jupoczp5Ucg0ckE8ADoVk66RjVgZaAK8p0b-put9ucbJ4XH4lIyBGUCRx8enscwySDTela5rZDsl_ZRE5lI2cWWzqHvgLjJ0GbHaT5YKvQiwIvjFBmHTjdpmEVxGi3AImIaC2qfoMaDRcnIX3fFjaKUOwglarIgLiF9mT_jtfp_wMachlWbhQyBOth19nelTOMfpv2U"  # Replace with your RHACS API token

    # Setup headers
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
    }

    # Full URL
    deployment_id = "d766a0c7-ee8b-441d-b627-08ec5930ae50"
    url = f"{RHACS_CENTRAL_URL}{API_ENDPOINT}/{deployment_id}"

    # Make the GET request
    try:
        response = requests.get(
            url, headers=headers, verify=False
        )  # verify=False skips SSL verification (only for testing!)
        response.raise_for_status()  # Raise error if the request failed

        # Parse JSON
        deployments = response.json()

        # Pretty print the results
        return json.dumps(deployments, indent=2)

    except requests.exceptions.RequestException as e:
        print(f"Error querying RHACS API: {e}")


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
        "What are the deployment risks for the cert-manager deployment? Suggest remediations for the risks"
    )

    print(result.output)