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
    """
    Create and return the emotion agent with endpoints for proper registration.
    
    Returns:
        Agent: The emotion agent instance with properly configured endpoints.
    """
    # Use a fixed port for the emotion agent
    port = 8101
    
    agent = Agent(
        name="emotion_agent",
        seed=os.getenv("EMOTION_AGENT_SEED", "emotion_agent_seed"),
        port=port,
        endpoint=f"http://127.0.0.1:{port}"
    )
    
    return agent

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

# Define a response model
class EmotionResponse(BaseModel):
    status: str
    emotion: str = None
    error: str = None

# Define a recommendations request model
class RecommendationsRequest(BaseModel):
    operation: str
    emotion: str
    requester: str

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
            # Use structured response with model_dump() instead of dict()
            response = EmotionResponse(status="error", error="Text is required for emotion classification")
            await ctx.send(sender, response.model_dump())
            return
        
        emotion_agent_instance = EmotionAgent()
        emotion = emotion_agent_instance.classify_emotion(text)
        
        # Send the classified emotion to the sender using model_dump()
        response = EmotionResponse(status="success", emotion=emotion)
        await ctx.send(sender, response.model_dump())
        
        # If spotify_agent is specified, also send to it using model_dump()
        spotify_agent = msg.spotify_agent
        if spotify_agent:
            rec_request = RecommendationsRequest(
                operation="get_recommendations",
                emotion=emotion,
                requester=sender
            )
            await ctx.send(spotify_agent, rec_request.model_dump())
    
    else:
        response = EmotionResponse(status="error", error="Invalid operation")
        await ctx.send(sender, response.model_dump())

# Get the agent and include the protocol only when needed
def get_emotion_agent():
    global emotion_agent
    if emotion_agent is None:
        emotion_agent = create_emotion_agent()
        emotion_agent.include(emotion_protocol)
    return emotion_agent 