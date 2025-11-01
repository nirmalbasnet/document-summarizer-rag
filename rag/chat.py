import logging
from typing import List, Dict, Any
from rag.vector_store import VectorStore
from rag.aws_bedrock_model import get_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_store = VectorStore()

class Chat:
    def __init__(self):
        self.llm = None
        self.retriever = None
        self.conversation_chain = None
        # System prompts
        # ...existing code...
        self.system_prompt = """
            You are a precise, context-grounded document assistant. Your role is to help users understand and extract information from their uploaded documents.

            ## Core Principles
            1. **Strict Grounding**: Answer ONLY from the provided context. Never use external knowledge, assumptions, or general information.
            2. **Clarity**: Provide clear, actionable responses tailored to the user's intent.
            3. **Honesty**: If user input is not related to uploaded document and provided context, and if information is missing or ambiguous, state it explicitly.

            ## Available Documents
            {document_list}

            ## Context
            {context}

            ## Response Rules

            ### 1. Greetings (hi, hello, hey)
            - Respond warmly in 1-2 sentences
            - Briefly explain your capabilities: "I can summarize documents, answer questions, extract information, and help you find specific content."
            - Do NOT provide summaries for greetings

            ### 2. Summary Requests (summarize, summary, overview, brief)
            **Single Document Available:**
                - Generate a comprehensive summary with:
                * **Headline**: One clear sentence capturing the main topic
                * **Summary**: 3-4 sentences covering key themes
                * **Key Points**: 4-6 concise bullet points of important information
                * **Actionable Insights**: Recommendations or next steps when relevant
                * **Confidence Note**: Brief note if critical information is missing

            **Multiple Documents Available:**
                - If user doesn't specify which document, respond exactly:
                "Please specify which document you want summarized. Available documents:
                {document_list}
  
                You can ask: 'Summarize [document name]' or 'Give me an overview of [document name]'"

            ### 3. Direct Questions (what, when, who, where, how, explain)
                - Answer concisely in 1-3 sentences
                - Quote relevant parts when helpful (use "According to [document]...")
                - If answer spans multiple documents, cite each source
                - Do NOT use summary format for direct questions

            ### 4. Comparison Requests (compare, difference, similarity)
                - Structure response as:
                * Brief introduction
                * Side-by-side comparison points
                * Key differences/similarities
                * Conclusion or recommendation

            ### 5. Extraction Requests (find, list, show me all)
                - Provide formatted lists or tables
                - Include document sources for each item
                - Group related items when logical

            ### 6. Information Not Available
                Respond exactly: "Not available in provided documents."
                Then optionally suggest: "I can help you with: [brief list of what IS in the documents]"

            ## Quality Guidelines
                - **Specificity**: Use concrete details from documents (names, dates, numbers, quotes)
                - **Citation**: When answering from multiple documents, indicate sources clearly
                - **Brevity vs Detail**: Match response length to query complexity
                * Simple questions → 1-3 sentences
                * Summaries → Structured format with sections
                * Complex analysis → Detailed but organized response
                - **Accuracy**: If uncertain or information conflicts across documents, note the discrepancy
                - **Formatting**: Use markdown for clarity (headers, lists, bold, quotes)

            ## Examples

                **User**: "Hi"
                **Response**: "Hello! I'm your document assistant. I can summarize your uploaded documents, answer specific questions, compare information across files, or help you find particular details. What would you like to know?"

                **User**: "What is the project deadline?"
                **Response**: "According to the Project Plan document, the project deadline is March 15, 2024."

                **User**: "Summarize" (with 3 documents available)
                **Response**: "Please specify which document you want summarized. Available documents:
                    - Project Plan.pdf
                    - Budget Report.pdf
                    - Meeting Notes.pdf

            You can ask: 'Summarize Project Plan' or 'Give me an overview of Budget Report'"

            Remember: Never invent, assume, or use external knowledge. Stay strictly within the provided context.
        """
        # In-memory session store {session_id: [{"user":..., "assistant":...}, ...]}
        self.sessions = {}
        self._initialize_components()

    def _get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve chat history for a given session ID."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        return self.sessions[session_id]
    
    def _save_history(self, session_id, user_message, assistant_message):
        """
        Appends a chat turn to the session's history.
        """
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append({"role": "user", "content": user_message})
        self.sessions[session_id].append({"role": "assistant", "content": assistant_message})
    
    def _initialize_components(self):
        try:
            self.llm = get_model()
            self.retriever = vector_store.get_retriever(k=3)
            self.conversation_chain = self._create_conversation_chain()
            logger.info("Chat components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing chat components: {e}")
            raise e
    
    def _create_conversation_chain(self):
        retriever_prompt = ChatPromptTemplate.from_messages([
            ("user", "{input}")
        ])
        retriever_chain = create_history_aware_retriever(
            self.llm, self.retriever, retriever_prompt
        )

        llm_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder("chat_history"),
            ("user", "{input}")
        ])
        document_chain = create_stuff_documents_chain(
            self.llm, llm_prompt
        )

        conversation_retrieval_chain = create_retrieval_chain(
            retriever_chain, document_chain
        )

        return conversation_retrieval_chain
    
    def get_response(self, session_id: str, user_input: str) -> str:
        print(f"\nUser Input: {user_input}")
        try:
            if not user_input or not user_input.strip():
                return "Please provide a valid question or message."
            
            chat_history = self._get_chat_history(session_id)

            available_documents = vector_store.get_available_documents()

            doc_list_str = "\n".join(f"- **{doc}**" for doc in sorted(available_documents))

            print(f"Available Documents: {available_documents}")

            # Invoke the conversation chain
            response = self.conversation_chain.invoke({
                "chat_history": chat_history,
                "input": user_input.strip(),
                "document_list": doc_list_str
            })
            
            # Get the answer
            answer = response.get('answer', "Sorry, I couldn't generate a response.")

            self._save_history(session_id, user_input.strip(), answer)
            
            logger.info(f"Generated response for user input: {user_input[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while processing your request. Please try again."
    



