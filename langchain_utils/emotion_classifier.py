import os
from dotenv import load_dotenv
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

# Initialize OpenAI LLM
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0.3)

# Create a prompt template for emotion classification
emotion_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
    Analyze the following text and identify the primary emotion expressed.
    Return just a single word representing the emotion (e.g., happy, sad, excited, anxious, etc.).
    
    Text: {text}
    
    Emotion:
    """
)

# Create an LLM chain for emotion classification
emotion_chain = LLMChain(llm=llm, prompt=emotion_prompt)

def classify_emotion(text):
    """
    Classify the emotion expressed in the given text using LangChain's LLM.
    
    Args:
        text (str): The text to classify.
        
    Returns:
        str: A single word representing the detected emotion.
    """
    try:
        # Get the emotion from the LLM
        emotion = emotion_chain.run(text).strip().lower()
        
        # Standardize common emotion terms
        emotion_mapping = {
            "happiness": "happy",
            "sadness": "sad",
            "anger": "angry",
            "fear": "afraid",
            "surprise": "surprised",
            "disgust": "disgusted",
            "joy": "happy",
            "sorrow": "sad",
            "rage": "angry",
            "terror": "afraid",
            "amazement": "surprised"
        }
        
        # Return the standardized emotion or the original if not in mapping
        return emotion_mapping.get(emotion, emotion)
    
    except Exception as e:
        print(f"Error classifying emotion: {e}")
        return "neutral"  # Default emotion if classification fails 