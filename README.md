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

## Project Structure

```
mood-weather-playlist-creator/
├── agents/
│   ├── emotion_agent.py
│   ├── spotify_agent.py
│   ├── memory_agent.py
│   └── weather_agent.py
├── langchain_utils/
│   └── emotion_classifier.py
├── spotify_utils/
│   └── spotify_api.py
├── weather_utils/
│   └── weather_api.py
├── ui/
│   └── streamlit_app.py
├── main.py
├── requirements.txt
├── .env
└── README.md
```

## Installation

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd mood-weather-playlist-creator
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory with the following variables:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   OPENWEATHER_API_KEY=your_openweather_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

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

## Credits

- [uAgents](https://github.com/fetchai/uAgents) - For agent-based architecture
- [LangChain](https://github.com/hwchase17/langchain) - For emotion classification
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) - For music recommendations
- [OpenWeatherMap API](https://openweathermap.org/api) - For weather data

## License

MIT License 