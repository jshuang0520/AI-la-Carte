from fuzzywuzzy import fuzz

def calculate_similarity(string1: str, string2: str) -> float:
    """
    Calculate a similarity score between two input strings using fuzzywuzzy's ratio.

    The function returns a similarity score between 0 and 100, where 100 
    indicates an exact match and lower scores indicate less similarity.
    
    This score can be used, for example, to decide how confident you are that two 
    agency ID strings—coming from different datasets—refer to the same entity.

    Parameters:
    - string1: The first string to compare.
    - string2: The second string to compare.

    Returns:
    - A float representing the similarity score (0 to 100).
    """
    # Ensure both inputs are strings
    if not isinstance(string1, str) or not isinstance(string2, str):
        raise ValueError("Both inputs must be strings.")
    
    # Calculate similarity using fuzzywuzzy's ratio.
    score = fuzz.ratio(string1, string2)
    return score

# For quick testing:
if __name__ == "__main__":
    test_str1 = "15567-MOMK-01"
    test_str2 = "15567-MOMK-01 Academy of Hope"
    similarity = calculate_similarity(test_str1, test_str2)
    print(f"Similarity Score between these two strings: {similarity}")
    str_1 = "hope home, college park, MD, 20740"
    str_2 = "hopeless home, college park, MD, 20740"
    similarity = calculate_similarity(str_1, str_2)
    print(f"caution: similarity of '{str_1}' and '{str_2}' = {similarity}")

