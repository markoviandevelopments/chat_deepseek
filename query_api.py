import requests
import ast

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
    #user_prompt = input("Enter your question: ")
    user_prompt = 'make a list of 10 numbers, but for machine readability start with "@". So, e.g.: "@[3, 5, ...]. Do not include the "@" symbol before your final list!"'
    result = query_api(user_prompt)
    print("\nAnswer:", result)
    print("\n\n")
    indexx = result.find("@[")
    print(indexx)
    print("\n\n")
    for i in range(2, 100):
        if (result[indexx + i] == "]"):
            break
    
    print(result[indexx:(i + indexx)])
    print("\n\n")
    list = ast.literal_eval("[3, 2]")
    print(list[0])
