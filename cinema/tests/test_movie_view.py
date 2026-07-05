from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from cinema.models import Movie, Genre, Actor
from cinema.serializers import MovieListSerializer


MOVIE_URL = reverse("cinema:movie-list")

def sample_movie(**params) -> Movie:
    defaults = {
        "title": "Inception",
        "description": "Dream heist",
        "duration": 148,
    }
    defaults.update(params)
    return Movie.objects.create(**defaults)


def detail_url(movie_id):
    return reverse("cinema:movie-list", args=(movie_id,))


class UnauthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(MOVIE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email = "test@test.test",
            password = "testpassword"
        )
        self.client.force_authenticate(self.user)

    def test_movies_list(self):
        sample_movie()
        movie_with_genre_and_actor = sample_movie()

        genre = Genre.objects.create(name="Sci-Fi")
        actor = Actor.objects.create(
            first_name="Leonardo",last_name="DiCaprio")
        movie_with_genre_and_actor.genres.add(genre)
        movie_with_genre_and_actor.actors.add(actor)

        res = self.client.get(MOVIE_URL)
        movies = Movie.objects.all()
        serializer = MovieListSerializer(movies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_movies_by_title(self):
        movie_title_1 = sample_movie()
        movie_title_2 = sample_movie(title="Spectre")
        movie_title_3 = sample_movie(title="Forrest Gump")

        res = self.client.get(
            MOVIE_URL,
            {"title": f"{movie_title_2.title}"}
        )
        serializer_movie_title_1 = MovieListSerializer(movie_title_1)
        serializer_movie_title_2 = MovieListSerializer(movie_title_2)
        serializer_movie_title_3 = MovieListSerializer(movie_title_3)

        self.assertIn(serializer_movie_title_2.data, res.data)
        self.assertNotIn(serializer_movie_title_1.data, res.data)
        self.assertNotIn(serializer_movie_title_3.data, res.data)

    def test_filter_movies_by_genre(self):
        movie_without_genre = sample_movie()
        movie_with_genre_1 = sample_movie(title="Forrest Gump")
        movie_with_genre_2 = sample_movie(title="Spectre")

        genre_1 = Genre.objects.create(name="Drama")
        genre_2 = Genre.objects.create(name="Action")

        movie_with_genre_1.genres.add(genre_1)
        movie_with_genre_2.genres.add(genre_2)

        res = self.client.get(
            MOVIE_URL,
            {"genres": f"{genre_1.id},{genre_2.id}"}
        )

        serializer_without_genre = MovieListSerializer(movie_without_genre)
        serializer_movie_genre_1 = MovieListSerializer(movie_with_genre_1)
        serializer_movie_genre_2 = MovieListSerializer(movie_with_genre_2)

        self.assertIn(serializer_movie_genre_1.data, res.data)
        self.assertIn(serializer_movie_genre_2.data, res.data)
        self.assertNotIn(serializer_without_genre.data, res.data)
