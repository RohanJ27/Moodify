import os
import json
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Create the agent in a function to avoid import-time initialization
def create_memory_agent():
    return Agent(
        name="memory_agent",
        seed=os.getenv("MEMORY_AGENT_SEED", "memory_agent_seed"),
    )

# Create a lazy-loaded agent instance
memory_agent = None

class MemoryAgent:
    def __init__(self):
        """
        Initialize the MemoryAgent with LangChain's ConversationBufferMemory.
        Uses a dictionary to store user-specific memories.
        """
        self.memories = {}
        
    def create_user_memory(self, user_id):
        """
        Create a new memory instance for a user if it doesn't exist.
        
        Args:
            user_id (str): Unique identifier for the user.
        """
        if user_id not in self.memories:
            self.memories[user_id] = ConversationBufferMemory()
    
    def store_interaction(self, user_id, interaction):
        """
        Store user interaction in memory.
        
        Args:
            user_id (str): Unique identifier for the user.
            interaction (dict): Interaction data to store.
        """
        self.create_user_memory(user_id)
        
        # Convert interaction to string if it's a dictionary
        if isinstance(interaction, dict):
            interaction_str = json.dumps(interaction)
        else:
            interaction_str = str(interaction)
        
        # Store in LangChain memory
        self.memories[user_id].save_context(
            {"input": interaction_str},
            {"output": "Stored in memory"}
        )
        
        # Also store in file system for persistence
        self._save_to_file(user_id, interaction)
    
    def get_interactions(self, user_id):
        """
        Retrieve user interactions from memory.
        
        Args:
            user_id (str): Unique identifier for the user.
            
        Returns:
            list: List of stored interactions.
        """
        self.create_user_memory(user_id)
        
        # Get from LangChain memory
        memory_variables = self.memories[user_id].load_memory_variables({})
        
        # Also try to load from file system
        file_interactions = self._load_from_file(user_id)
        
        # Combine and return
        return {
            "langchain_memory": memory_variables,
            "file_interactions": file_interactions
        }
    
    def _save_to_file(self, user_id, interaction):
        """
        Save interaction to a file for persistence.
        
        Args:
            user_id (str): Unique identifier for the user.
            interaction (dict or str): Interaction data to store.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs("memory", exist_ok=True)
            
            # Load existing interactions
            interactions = self._load_from_file(user_id)
            
            # Add new interaction
            interactions.append(interaction)
            
            # Save to file
            with open(f"memory/{user_id}.json", "w") as f:
                json.dump(interactions, f)
        
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def _load_from_file(self, user_id):
        """
        Load interactions from a file.
        
        Args:
            user_id (str): Unique identifier for the user.
            
        Returns:
            list: List of stored interactions.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs("memory", exist_ok=True)
            
            # Load from file if it exists
            if os.path.exists(f"memory/{user_id}.json"):
                with open(f"memory/{user_id}.json", "r") as f:
                    return json.load(f)
        
        except Exception as e:
            print(f"Error loading from file: {e}")
        
        return []

# Create a Protocol for memory operations
memory_protocol = Protocol("memory")

# Define the message model using Pydantic
class MemoryRequest(BaseModel):
    operation: str
    user_id: str
    interaction: dict = None

@memory_protocol.on_message(model=MemoryRequest)
async def handle_memory_request(ctx: Context, sender: str, msg: MemoryRequest):
    """
    Handle incoming memory requests.
    
    Args:
        ctx (Context): Agent context.
        sender (str): Sender agent address.
        msg (MemoryRequest): Message containing the memory operation.
    """
    operation = msg.operation
    user_id = msg.user_id
    
    if not user_id:
        await ctx.send(sender, {"error": "User ID is required"})
        return
    
    memory_instance = MemoryAgent()
    
    if operation == "store":
        interaction = msg.interaction
        if interaction:
            memory_instance.store_interaction(user_id, interaction)
            await ctx.send(sender, {"status": "success", "message": "Interaction stored"})
        else:
            await ctx.send(sender, {"error": "Interaction data is required"})
    
    elif operation == "retrieve":
        interactions = memory_instance.get_interactions(user_id)
        await ctx.send(sender, {"status": "success", "interactions": interactions})
    
    else:
        await ctx.send(sender, {"error": "Invalid operation"})

# Get the agent and include the protocol only when needed
def get_memory_agent():
    global memory_agent
    if memory_agent is None:
        memory_agent = create_memory_agent()
        memory_agent.include(memory_protocol)
    return memory_agent 