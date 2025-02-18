import requests
import ast
import re
import json

def query_api(user_prompt, temperature=0.7):
    url = "http://50.188.120.138:5049/api/deepseek"
    params = {
        "prompt": user_prompt,
        "temperature": temperature  # Add temperature to the request
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        # Extract and clean the response
        answer = data.get("response", "").strip()
        # answer = answer.replace("<think>", "").replace("</think>", "").strip()
        
        # raw_answer = data.get("response", "").strip()

        # Remove <think> sections safely
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()

 

        return answer if answer else "No response received."
    
    except requests.RequestException as e:
        return f"Error: {e}"

if __name__ == "__main__":
    theme = input("Enter the theme: ")
    temp = float(input("Enter the temperature (default 0.7): ")) 

    user_prompt = 'Please generate a set of 2 dimensional arrays for the use of lighting up some leds. Make the theme: ' + theme + '. Each array should be IMMEDIATELY preceeded by an "@" symbol and be 10 items long. Such as, for example, "@[[255, 255, 255], [225, 235, 115], ..., [0, 124, 42]]".  Value in each tuple should be between 0 and 255, inclusive. Ten tuples long a piece. Go China!'
    result = query_api(user_prompt, temperature=temp)
    print("\nAnswer:", result)
    print("\n\n")
    result = result.replace("\n", "").replace(" ", "")

    indexx = result.find("@[")
    print(indexx)
    print("\n\n")
    for i in range(2, 1000):
        if (result[(indexx + i) : (indexx + i + 2)] == "]]"):
            break
    
    list_str = result[(indexx + 1):(i + indexx + 2)]
    print(list_str)
    print("\n\n")
    list = ast.literal_eval(list_str)

    passed = False
    if (len(list) == 10 and len(list[0]) == 3):
        passed = True
    
    print(passed)
    if passed:
        with open("led_pattern.json", "w") as json_file:
            json.dump(list, json_file, indent=4)
        print("LED pattern saved to led_pattern.json")
