import os
import sys
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_utils.emotion_classifier import classify_emotion

# Load environment variables
load_dotenv()

# Create the agent in a function to avoid import-time initialization
def create_emotion_agent():
    return Agent(
        name="emotion_agent",
        seed=os.getenv("EMOTION_AGENT_SEED", "emotion_agent_seed"),
    )

# Create a lazy-loaded agent instance
emotion_agent = None

class EmotionAgent:
    def __init__(self):
        """
        Initialize EmotionAgent to classify emotions from text input.
        """
        pass

    def classify_emotion(self, text):
        """
        Classify the emotion expressed in the given text.
        
        Args:
            text (str): The text to classify.
            
        Returns:
            str: The detected emotion.
        """
        try:
            # Use LangChain to classify the emotion
            emotion = classify_emotion(text)
            return emotion
        
        except Exception as e:
            print(f"Error classifying emotion: {e}")
            return "neutral"  # Default emotion if classification fails

# Create a Protocol for emotion operations
emotion_protocol = Protocol("emotion")

# Define the message model using Pydantic
class EmotionRequest(BaseModel):
    operation: str
    text: str = None
    spotify_agent: str = None

@emotion_protocol.on_message(model=EmotionRequest)
async def handle_emotion_request(ctx: Context, sender: str, msg: EmotionRequest):
    """
    Handle incoming emotion classification requests.
    
    Args:
        ctx (Context): Agent context.
        sender (str): Sender agent address.
        msg (EmotionRequest): Message containing the emotion classification request.
    """
    operation = msg.operation
    
    if operation == "classify_emotion":
        text = msg.text
        
        if not text:
            await ctx.send(sender, {"error": "Text is required for emotion classification"})
            return
        
        emotion_agent_instance = EmotionAgent()
        emotion = emotion_agent_instance.classify_emotion(text)
        
        # Send the classified emotion to the sender
        await ctx.send(sender, {
            "status": "success",
            "emotion": emotion
        })
        
        # If spotify_agent is specified, also send to it
        spotify_agent = msg.spotify_agent
        if spotify_agent:
            await ctx.send(spotify_agent, {
                "operation": "get_recommendations",
                "emotion": emotion,
                "requester": sender
            })
    
    else:
        await ctx.send(sender, {"error": "Invalid operation"})

# Get the agent and include the protocol only when needed
def get_emotion_agent():
    global emotion_agent
    if emotion_agent is None:
        emotion_agent = create_emotion_agent()
        emotion_agent.include(emotion_protocol)
    return emotion_agent 