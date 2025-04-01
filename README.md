# Mood & Weather Playlist Creator

A full-stack Python application that creates personalized Spotify playlists based on user's mood or current weather conditions.

## Features

- **Mood-based Playlist Creation**: Enter your mood and get a customized Spotify playlist that matches your emotional state.
- **Weather-based Playlist Creation**: Enter your location and get a playlist that matches the current weather.
- **Spotify Integration**: Connect your Spotify account to create and save playlists directly to your profile.
- **Intelligent Playlist Generation**: Uses OpenAI's language models to understand emotions and match them with appropriate music.
- **Sleek UI**: Modern, responsive user interface built with Streamlit.

## Technology Stack

- **uAgents & Agentverse**: For building autonomous agents that handle specific tasks
- **LangChain**: For emotion classification and persistent memory
- **Spotify API**: For music recommendations and playlist creation
- **OpenWeatherMap API**: For retrieving current weather data
- **Streamlit**: For building the user interface


1. **Start the agent system**:
   ```
   python main.py
   ```

2. **Run the Streamlit app**:
   ```
   streamlit run ui/streamlit_app.py
   ```

3. **Use the application**:
   - Connect your Spotify account
   - Choose between mood-based or weather-based playlist creation
   - Enter your mood or location
   - Generate and save your personalized playlist

## How It Works

1. **Mood-based flow**:
   - User enters their mood
   - EmotionAgent uses LangChain and OpenAI to classify the text into an emotion
   - SpotifyAgent receives the emotion and generates a playlist
   - User can save the playlist to their Spotify account

2. **Weather-based flow**:
   - User enters their location
   - WeatherAgent queries OpenWeatherMap API to get current weather
   - Weather condition is mapped to an emotion
   - SpotifyAgent receives the emotion and generates a playlist
   - User can save the playlist to their Spotify account
