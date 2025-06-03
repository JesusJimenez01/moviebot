import os
import requests
import logging
import random
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from fuzzywuzzy import fuzz, process
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(BASE_DIR, '.env')

load_dotenv(dotenv_path)
logger = logging.getLogger(__name__)


class ActionRecommendMovie(Action):
    def name(self) -> Text:
        return "action_recommend_movie"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        genre = tracker.get_slot('genre')
        api_key = os.getenv('TMDB_API_KEY')
        
        if not api_key:
            dispatcher.utter_message(text="Error de configuración. Contacta al administrador.")
            return []

        try:
            if genre:
                genre_id = self.get_genre_id_fuzzy(genre)
                url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}&language=es-ES&sort_by=vote_average.desc&vote_count.gte=100"
            else:
                # Si no hay género específico, recomendar películas populares bien valoradas
                url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=es-ES&sort_by=vote_average.desc&vote_count.gte=500"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                # Seleccionar película aleatoria de las top 10
                movies = data['results'][:10]
                movie = random.choice(movies)
                
                title = movie.get('title', 'Título no disponible')
                overview = movie.get('overview', 'Descripción no disponible')
                rating = movie.get('vote_average', 0)
                release_date = movie.get('release_date', '')
                year = release_date.split('-')[0] if release_date else ''
                
                message = f"🎬 **{title}** ({year})\n"
                message += f"⭐ Puntuación: {rating}/10\n\n"
                message += f"📝 {overview[:400]}..."
                
                dispatcher.utter_message(text=message)
                dispatcher.utter_message(text="¿Te gustaría otra recomendación o algo de un género específico?")
                
            else:
                dispatcher.utter_message(text="No encontré películas con esos criterios. ¿Quieres probar con otro género?")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error API: {e}")
            dispatcher.utter_message(text="Disculpa, hay problemas de conexión. Inténtalo más tarde.")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            dispatcher.utter_message(text="Ocurrió un error inesperado. ¿Puedes intentar de nuevo?")
        
        return []

    def get_genre_id_fuzzy(self, genre_name: str) -> int:
        """Usa fuzzy matching para encontrar el género más similar"""
        genre_map = {
            'acción': 28, 'action': 28,
            'aventura': 12, 'adventure': 12,
            'comedia': 35, 'comedy': 35, 'humor': 35, 'divertida': 35,
            'drama': 18, 'dramática': 18,
            'terror': 27, 'horror': 27, 'miedo': 27, 'suspenso': 27,
            'romance': 10749, 'romántica': 10749, 'amor': 10749,
            'ciencia ficción': 878, 'sci-fi': 878, 'ficción': 878, 'futurista': 878,
            'animación': 16, 'animada': 16, 'dibujos': 16,
            'crimen': 80, 'criminal': 80, 'policíaca': 80,
            'documental': 99, 'documentary': 99,
            'familia': 10751, 'familiar': 10751, 'niños': 10751,
            'fantasía': 14, 'fantasy': 14, 'fantástica': 14, 'magia': 14,
            'historia': 36, 'histórica': 36, 'época': 36,
            'música': 10402, 'musical': 10402,
            'misterio': 9648, 'thriller': 53, 'suspense': 53,
            'guerra': 10752, 'bélica': 10752,
            'western': 37, 'oeste': 37
        }
        
        # Fuzzy matching para encontrar el género más similar
        best_match = process.extractOne(
            genre_name.lower(), 
            genre_map.keys(),
            scorer=fuzz.ratio,
            score_cutoff=50
        )
        
        if best_match:
            return genre_map[best_match[0]]
        return 28  # Default: acción


class ActionSearchMovie(Action):
    def name(self) -> Text:
        return "action_search_movie"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        movie_title = tracker.get_slot('movie_title')
        api_key = os.getenv('TMDB_API_KEY')
        
        if not movie_title:
            dispatcher.utter_message(text="¿Qué película quieres buscar?")
            return []
            
        if not api_key:
            dispatcher.utter_message(text="Error de configuración.")
            return []

        try:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_title}&language=es-ES"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                movie = data['results'][0]  # Primera coincidencia
                
                title = movie.get('title', 'Título no disponible')
                overview = movie.get('overview', 'Descripción no disponible')
                rating = movie.get('vote_average', 0)
                release_date = movie.get('release_date', '')
                year = release_date.split('-')[0] if release_date else ''
                
                message = f"🎬 **{title}** ({year})\n"
                message += f"⭐ Puntuación: {rating}/10\n\n"
                message += f"📝 {overview}"
                
                dispatcher.utter_message(text=message)
                
            else:
                dispatcher.utter_message(text=f"No encontré información sobre '{movie_title}'. ¿Puedes verificar el título?")
                
        except Exception as e:
            logger.error(f"Error buscando película: {e}")
            dispatcher.utter_message(text="No pude realizar la búsqueda. Inténtalo más tarde.")
        
        return [SlotSet("movie_title", None)]


class ActionGetPopularMovies(Action):
    def name(self) -> Text:
        return "action_get_popular_movies"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        api_key = os.getenv('TMDB_API_KEY')
        
        if not api_key:
            dispatcher.utter_message(text="Error de configuración.")
            return []

        try:
            url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=es-ES"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                movies = data['results'][:5]  # Top 5
                
                message = "🔥 **Películas populares del momento:**\n\n"
                for i, movie in enumerate(movies, 1):
                    title = movie.get('title', 'Sin título')
                    year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                    rating = movie.get('vote_average', 0)
                    
                    message += f"{i}. **{title}** ({year}) - ⭐ {rating}/10\n"
                
                dispatcher.utter_message(text=message)
                dispatcher.utter_message(text="¿Te interesa alguna en particular?")
                
            else:
                dispatcher.utter_message(text="No pude obtener las películas populares en este momento.")
                
        except Exception as e:
            logger.error(f"Error obteniendo películas populares: {e}")
            dispatcher.utter_message(text="No pude obtener las películas populares. Inténtalo más tarde.")
        
        return []


class ActionAddToWatchlist(Action):
    def name(self) -> Text:
        return "action_add_to_watchlist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        movie_title = tracker.get_slot('movie_title')
        
        if movie_title:
            dispatcher.utter_message(text=f"✅ He añadido '{movie_title}' a tu lista para ver después. ¡No olvides verla!")
        else:
            dispatcher.utter_message(text="✅ ¡Perfecto! Recordaré esa película para ti.")
        
        return []


class ActionFindMovieByDescription(Action):
    def name(self) -> Text:
        return "action_find_movie_by_description"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        description = tracker.get_slot('description')
        api_key = os.getenv('TMDB_API_KEY')
        
        if not description:
            dispatcher.utter_message(text="Describe la película que buscas. Por ejemplo: 'una película sobre un sueño dentro de un sueño'")
            return []
            
        if not api_key:
            dispatcher.utter_message(text="Error de configuración.")
            return []

        try:
            # Buscar por palabras clave en la descripción
            keywords = self.extract_keywords(description)
            
            # Intentar búsqueda por palabras clave primero
            results = []
            for keyword in keywords[:3]:  # Solo las 3 más relevantes
                url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={keyword}&language=es-ES"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        results.extend(data['results'][:5])
            
            if results:
                # Eliminar duplicados y ordenar por popularidad
                unique_movies = {}
                for movie in results:
                    movie_id = movie.get('id')
                    if movie_id not in unique_movies:
                        unique_movies[movie_id] = movie
                
                # Tomar las 3 más populares
                sorted_movies = sorted(unique_movies.values(), 
                                     key=lambda x: x.get('popularity', 0), 
                                     reverse=True)[:3]
                
                if len(sorted_movies) == 1:
                    movie = sorted_movies[0]
                    title = movie.get('title', 'Título no disponible')
                    overview = movie.get('overview', 'Descripción no disponible')
                    rating = movie.get('vote_average', 0)
                    release_date = movie.get('release_date', '')
                    year = release_date.split('-')[0] if release_date else ''
                    
                    message = f"🎬 **{title}** ({year})\n"
                    message += f"⭐ Puntuación: {rating}/10\n\n"
                    message += f"📝 {overview}"
                    
                    dispatcher.utter_message(text=f"Creo que buscas esta película:\n\n{message}")
                else:
                    message = "🔍 **Estas películas podrían coincidir con tu descripción:**\n\n"
                    for i, movie in enumerate(sorted_movies, 1):
                        title = movie.get('title', 'Sin título')
                        year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
                        rating = movie.get('vote_average', 0)
                        
                        message += f"{i}. **{title}** ({year}) - ⭐ {rating}/10\n"
                    
                    dispatcher.utter_message(text=message)
                    dispatcher.utter_message(text="¿Alguna de estas es la que buscabas?")
            else:
                dispatcher.utter_message(text="No pude encontrar películas que coincidan con esa descripción. ¿Puedes darme más detalles o palabras clave?")
                
        except Exception as e:
            logger.error(f"Error buscando por descripción: {e}")
            dispatcher.utter_message(text="No pude realizar la búsqueda. Inténtalo más tarde.")
        
        return [SlotSet("description", None)]

    def extract_keywords(self, description: str) -> List[str]:
        """Extrae palabras clave relevantes de la descripción"""
        # Palabras comunes a ignorar
        stop_words = {
            'una', 'un', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con', 'por', 'para',
            'que', 'es', 'son', 'está', 'están', 'tiene', 'tienen', 'película', 'pelicula',
            'film', 'movie', 'sobre', 'acerca', 'trata', 'habla', 'cuenta', 'narra'
        }
        
        # Limpiar y separar palabras
        words = description.lower().replace(',', ' ').replace('.', ' ').split()
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Priorizar palabras más largas (más específicas)
        keywords.sort(key=len, reverse=True)
        
        return keywords[:5]  # Máximo 5 palabras clave


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        fallback_messages = [
            "No estoy seguro de entender. Puedo recomendarte películas por género o ayudarte a encontrar una película por su descripción.",
            "¿Podrías ser más específico? Intenta con: 'recomiéndame una película de terror' o 'busco una película sobre viajes en el tiempo'.",
            "No entendí bien. Puedo ayudarte a encontrar películas. ¿Qué tipo de película te gustaría ver?"
        ]
        
        message = random.choice(fallback_messages)
        dispatcher.utter_message(text=message)
        
        return []
