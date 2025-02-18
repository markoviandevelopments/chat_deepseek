import requests

def query_api(user_prompt):
    url = "http://50.188.120.138:5049/api/deepseek"
    params = {"prompt": user_prompt}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        # Extract and clean the response
        answer = data.get("response", "").strip()
        answer = answer.replace("<think>", "").replace("</think>", "").strip()
        
        return answer if answer else "No response received."
    
    except requests.RequestException as e:
        return f"Error: {e}"

if __name__ == "__main__":
    user_prompt = input("Enter your question: ")
    result = query_api(user_prompt)
    print("\nAnswer:", result)
    print("\n\n")
    print(result.find("@["))
