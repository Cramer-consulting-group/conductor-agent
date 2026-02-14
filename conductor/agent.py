"""
Conductor agent that uses RAG to answer questions with context from all platforms.
"""

from typing import List, Dict, Any
from openai import OpenAI
from knowledge_base.retrieval import ConversationRetriever
from config.settings import settings
from utils.logger import logger


class ConductorAgent:
    """Main conductor agent with RAG-based question answering."""
    
    def __init__(self):
        """Initialize the conductor agent."""
        self.retriever = ConversationRetriever()
        self.client = None
        self.model = settings.conductor_model
        
        logger.info(f"Initialized conductor agent with model: {self.model}")
    
    def _init_client(self):
        """Lazy initialize OpenAI client."""
        if not self.client:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
            self.client = OpenAI(api_key=settings.openai_api_key)
    
    def chat(
        self,
        query: str,
        platform_filter: str = None,
        max_context_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Answer a query using RAG with conversation history.
        
        Args:
            query: User question
            platform_filter: Optional platform to filter (chatgpt, gemini, grok, antigravity)
            max_context_tokens: Maximum tokens for context
            
        Returns:
            Dict with 'response', 'sources', and 'context_used'
        """
        self._init_client()
        
        # Retrieve relevant context
        logger.info(f"Processing query: {query[:100]}...")
        
        results = self.retriever.search_conversations(
            query=query,
            n_results=5,
            platform_filter=platform_filter
        )
        
        # Format context
        context_parts = []
        sources = []
        
        for result in results:
            meta = result['metadata']
            content = result['content']
            
            source_info = {
                'platform': meta['platform'],
                'title': meta['title'],
                'conversation_id': meta.get('conversation_id', ''),
                'score': result['score']
            }
            sources.append(source_info)
            
            # Add to context
            context_parts.append(
                f"[Source: {meta['platform'].upper()} - {meta['title']}]\n{content}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build prompt
        system_prompt = """You are a helpful AI assistant with access to the user's conversation history across multiple AI platforms (ChatGPT, Gemini, Grok, and Antigravity).

Your role is to:
1. Answer questions using the provided context from past conversations
2. Cite which platform and conversation the information came from
3. Synthesize information from multiple sources when relevant
4. Be honest when the context doesn't contain the answer

Always mention the source platform (ChatGPT/Gemini/Grok/Antigravity) when referencing information from the context."""

        user_prompt = f"""Based on my conversation history, please answer this question:

{query}

Here is the relevant context from your past conversations:

{context}

Please provide a helpful answer based on this context. Cite which conversations/platforms you're referencing."""

        # Get completion
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                'response': answer,
                'sources': sources,
                'context_used': len(context),
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def stream_chat(
        self,
        query: str,
        platform_filter: str = None
    ):
        """
        Stream a chat response (for CLI display).
        
        Args:
            query: User question
            platform_filter: Optional platform filter
            
        Yields:
            Response chunks
        """
        self._init_client()
        
        # Retrieve context
        results = self.retriever.search_conversations(
            query=query,
            n_results=5,
            platform_filter=platform_filter
        )
        
        # Format context and sources
        context_parts = []
        sources = []
        
        for result in results:
            meta = result['metadata']
            content = result['content']
            
            sources.append({
                'platform': meta['platform'],
                'title': meta['title'],
                'score': result['score']
            })
            
            context_parts.append(
                f"[Source: {meta['platform'].upper()} - {meta['title']}]\n{content}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build prompt
        system_prompt = """You are a helpful AI assistant with access to the user's conversation history across multiple AI platforms (ChatGPT, Gemini, Grok, and Antigravity).

Your role is to:
1. Answer questions using the provided context from past conversations
2. Cite which platform and conversation the information came from
3. Synthesize information from multiple sources when relevant
4. Be honest when the context doesn't contain the answer

Always mention the source platform when referencing information."""

        user_prompt = f"""Based on my conversation history, please answer this question:

{query}

Here is the relevant context from your past conversations:

{context}

Please provide a helpful answer based on this context. Cite which conversations/platforms you're referencing."""

        # Stream response
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            # First yield sources
            yield {'type': 'sources', 'data': sources}
            
            # Then stream response
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {'type': 'content', 'data': chunk.choices[0].delta.content}
                    
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {'type': 'error', 'data': str(e)}


if __name__ == "__main__":
    # Test the conductor
    conductor = ConductorAgent()
    
    result = conductor.chat("What projects have I worked on?")
    
    print("Response:")
    print(result['response'])
    print(f"\nSources: {len(result['sources'])}")
    for source in result['sources']:
        print(f"  - {source['platform'].upper()}: {source['title']} (score: {source['score']:.2f})")
