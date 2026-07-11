import os
import json
import time
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class CuratedArticle(BaseModel):
    title: str = Field(description="The title of the selected article.")
    url: str = Field(description="The URL of the selected article.")
    topic: str = Field(description="The topic name for the current week.")
    vocab_words: List[str] = Field(description="Exactly 5 interesting or challenging vocabulary words from the article. Bare words only, no translations, parts of speech or definitions.")
    phrases: List[str] = Field(description="Exactly 10 useful phrases, collocations or sentence structures from the article. Bare phrases only, no translations or definitions.")
    story_passage: Optional[str] = Field(None, description="A very simple, short paragraph (50-80 words) using some of the extracted new words and phrases in an everyday, conversational context suitable for kids. If not possible, leave empty or omit.")

def curate_article(candidates: list[dict], weekly_topic: str, mock: bool = False) -> Optional[dict]:
    """Sends candidate articles and the weekly topic to Gemini to select and extract vocabulary/phrases."""
    if mock or os.environ.get("USE_MOCK", "").lower() == "true":
        return _get_mock_curation(candidates, weekly_topic)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set in environment variables.")
        return None
        
    if not candidates:
        logger.warning("No candidate articles available for curation.")
        return None
        
    # Format candidate articles for prompt
    articles_text = ""
    for idx, art in enumerate(candidates, start=1):
        articles_text += f"[{idx}] Title: {art['title']}\nURL: {art['url']}\nSummary: {art['summary']}\n\n"
        
    system_prompt = f"""You are a friendly English learning assistant for Vietnamese children aged 8-14 (Grades 1-9 / Cấp 1, Cấp 2).

This week's topic: {weekly_topic}

Given the list of articles below, select ONE article that:
1. Best matches this week's topic. If no article matches well, pick the most interesting one for kids (fallback).
2. Is age-appropriate — no violence, politics, or adult content.
3. Is short and engaging for children.

For the selected article, extract exactly 5 new vocabulary words, exactly 10 useful phrases or sentence structures to help children learn, and write a very simple everyday short story utilizing these terms.

Detailed guidelines:
- vocab_words: Exactly 5 interesting or challenging vocabulary words from the article. List ONLY the bare words — no definitions, no translations, no parts of speech, no phonetics. Example: ["discover", "river", "climate", "melt", "ground"].
- phrases: Exactly 10 useful phrases, collocations, or sentence structures from the article. List ONLY the bare phrases — no translations or explanations. Example: ["turn orange", "due to climate change", "melting ice"].
- story_passage: A very simple, short paragraph (50-80 words) using some of the extracted new words and phrases in an everyday, conversational context suitable for kids. It should be highly simple, natural, and helpful for understanding how to use the words in daily conversation.

Candidate Articles:
{articles_text}
"""

    # Determine models list starting from GEMINI_MODEL_LIST/GEMINI_MODELS/GEMINI_MODEL down to fallbacks
    models_to_try = []
    
    env_model_list = os.environ.get("GEMINI_MODEL_LIST")
    if env_model_list:
        models_to_try.extend([m.strip() for m in env_model_list.split(",") if m.strip()])
        
    env_models = os.environ.get("GEMINI_MODELS")
    if env_models:
        for m in env_models.split(","):
            m_clean = m.strip()
            if m_clean and m_clean not in models_to_try:
                models_to_try.append(m_clean)
        
    env_model = os.environ.get("GEMINI_MODEL")
    if env_model and env_model not in models_to_try:
        models_to_try.append(env_model)
        
    priority_fallbacks = [
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.5-flash"
    ]
    for model in priority_fallbacks:
        if model not in models_to_try:
            models_to_try.append(model)

    logger.info(f"Models to try in order: {models_to_try}")

    for model_name in models_to_try:
        # We try 2 attempts per model (first try, then wait 1 min and retry 1 time)
        for attempt in range(2):
            logger.info(f"Attempting curation with model '{model_name}' (Attempt {attempt + 1}/2)...")
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=system_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CuratedArticle,
                        temperature=0.7,
                    )
                )
                
                if not response.text:
                    raise ValueError("Empty response text from Gemini API")
                    
                # Parse & validate response
                result_json = json.loads(response.text)
                # Basic validation of schema structure
                if "title" in result_json and "url" in result_json and ("story_passage" in result_json or "passage" in result_json):
                    logger.info(f"Gemini curation successful! Selected article: '{result_json['title']}' using model '{model_name}'")
                    return result_json
                else:
                    raise ValueError("Invalid structure in Gemini response JSON: missing title, url, or story_passage")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} with model '{model_name}' failed: {e}")
                if attempt == 0:
                    logger.info("Waiting 60 seconds (1 minute) before retrying this model...")
                    time.sleep(60)
                else:
                    logger.warning(f"Model '{model_name}' failed after retry.")
                    
        # If we reach here, both attempts on model_name failed. It will proceed to next model in loop.
        logger.info(f"Moving to next fallback model due to failures with '{model_name}'...")

    logger.error("All models in list failed. Gemini curation returned no results.")
    return None

def _get_mock_curation(candidates: list[dict], weekly_topic: str) -> dict:
    """Helper to return a mock response when in mock mode, keeping curate_article clean."""
    logger.info("Using mock curation mode.")
    selected = candidates[0] if candidates else {
        "title": "Why are Arctic rivers turning orange?", 
        "url": "https://www.sciencejournalforkids.org/articles/why-are-arctic-rivers-turning-orange/"
    }
    return {
        "title": selected.get("title", "Why are Arctic rivers turning orange?"),
        "url": selected.get("url", "https://www.sciencejournalforkids.org/articles/why-are-arctic-rivers-turning-orange/"),
        "topic": weekly_topic,
        "vocab_words": [
            "discover",
            "permafrost",
            "chemical",
            "orange",
            "river"
        ],
        "phrases": [
            "turn orange",
            "due to climate change",
            "arctic region",
            "release into the water",
            "harm the fish",
            "melting ice",
            "frozen ground",
            "natural chemicals",
            "protect our Earth",
            "learning about science"
        ],
        "story_passage": "Yesterday, we decided to protect our Earth. We started by learning about science. We saw that the ice in the arctic region is melting, and the ground is changing. It is important to know about natural chemicals so we don't harm the fish."
    }
