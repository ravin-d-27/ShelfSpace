from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from google.genai import errors as genai_errors
from requests import Response
from unittest.mock import patch
from books import views


class GeminiViewsTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("books.views.render")
    @patch("books.views._generate_ai_text")
    def test_recommend_uses_prompt_suffix_and_renders_response(self, mock_generate_ai_text, mock_render):
        mock_generate_ai_text.return_value = "Dune — Frank Herbert"
        mock_render.return_value = HttpResponse("ok")
        request = self.factory.post("/books/recommend/", {"input_question": "sci-fi"})

        response = views.recommend.__wrapped__(request)

        self.assertEqual(response.status_code, 200)
        mock_generate_ai_text.assert_called_once_with(
            "sci-fi\n\nOnly Type the Book Name and Author. Not Any other thing"
        )
        mock_render.assert_called_once_with(
            request,
            "books/recommender.html",
            {"response": "Dune — Frank Herbert"},
        )

    @patch("books.views.render")
    @patch("books.views._generate_ai_text")
    def test_ask_me_anything_renders_generated_response(self, mock_generate_ai_text, mock_render):
        mock_generate_ai_text.return_value = "Generated answer"
        mock_render.return_value = HttpResponse("ok")
        request = self.factory.post("/books/ask/", {"input_question": "What is AI?"})

        response = views.ask_me_anything.__wrapped__(request)

        self.assertEqual(response.status_code, 200)
        mock_generate_ai_text.assert_called_once_with("What is AI?")
        mock_render.assert_called_once_with(
            request,
            "books/gemini.html",
            {"response": "Generated answer"},
        )

    @patch("books.views.genai.Client")
    def test_generate_ai_text_handles_quota_errors(self, mock_client):
        response = Response()
        response.status_code = 429
        response._content = b'{"error":{"message":"quota exceeded"}}'
        mock_client.return_value.models.generate_content.side_effect = genai_errors.APIError(429, response)

        response_text = views._generate_ai_text("recommend me a book")

        self.assertEqual(
            response_text,
            "Gemini is currently rate-limited. Please try again in a few moments.",
        )
