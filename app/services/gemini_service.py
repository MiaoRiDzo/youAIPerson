import os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool

# --- Gemini API Configuration ---
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
print(f"🔑 Gemini API key configured successfully")

# Get model name from environment
MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')
print(f"🤖 Using Gemini model: {MODEL_NAME}")

# --- Tool Definition for Function Calling ---
MANAGE_HOOKS_TOOL = Tool(
    function_declarations=[
        {
            "name": "manage_user_memory_hooks",
            "description": "Добавляет, обновляет или удаляет факты (хуки) о пользователе на основе анализа сообщения. Используется для поддержания актуальной информации о пользователе. Если пользователь выражает пожелания к стилю общения (например, 'пиши покороче', 'можно на ты', 'отвечай сухо'), запоминай это как отдельный хук. Извлекай не только факты, но и события, перемены, отношения, эмоции, если они важны для понимания пользователя (например, 'кот переехал к родителям', 'я начал заниматься HTML', 'я стал чаще гулять').",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "hooks_to_add": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Список новых фактов о пользователе, которые нужно запомнить. Включай сюда и пожелания к стилю общения, и любые события, перемены, отношения, эмоции."
                    },
                    "hooks_to_update": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "old_hook_text": {"type": "STRING"},
                                "new_hook_text": {"type": "STRING"}
                            },
                            "required": ["old_hook_text", "new_hook_text"]
                        },
                        "description": "Список фактов для обновления. Указывает старый текст и новый текст."
                    },
                    "hooks_to_delete": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Список фактов, которые стали неактуальны и их нужно удалить."
                    }
                }
            }
        }
    ]
)

# --- Gemini Model Initialization ---
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    tools=[MANAGE_HOOKS_TOOL]
)

# --- Main Analysis Function ---
async def analyze_and_manage_hooks(message_text: str, existing_hooks: list[str]):
    """
    Analyzes user message and decides whether to call the memory management function.
    """
    system_prompt = (
        "Ты — ядро памяти ассистента. Твоя задача — анализировать сообщение пользователя в контексте "
        "фактов, которые ты уже знаешь о нём (`existing_hooks`). На основе нового сообщения решай, нужно ли "
        "добавить, обновить или удалить какие-либо факты, чтобы профиль пользователя был актуальным. "
        "Вызывай функцию `manage_user_memory_hooks` для выполнения этих действий. "
        "Не вызывай функцию, если сообщение является простым вопросом, общей командой или не содержит "
        "новой или обновленной личной информации, которую стоит запомнить. "
        "Если пользователь явно или неявно выражает пожелания к стилю общения (например, 'пиши покороче', 'можно на ты', 'отвечай сухо'), запоминай это как отдельный хук. "
        "Если пользователь сообщает о событиях, изменениях, перемещениях, новых отношениях, эмоциях (например, 'кот переехал к родителям', 'я начал заниматься HTML', 'я стал чаще гулять'), обязательно добавляй это как отдельный хук. "
        "Пример: из сообщения 'Какой выбрать корм для стерилизованного кота 1.5 года?' извлеки три факта: 'У пользователя есть кот', 'Кот стерилизован', 'Коту 1.5 года'."
        f"Вот известные на данный момент факты о пользователе: {existing_hooks}"
    )
    
    try:
        response = await model.generate_content_async(
            system_prompt + "\n\nНовое сообщение от пользователя: " + message_text,
            generation_config=GenerationConfig(temperature=0.1)
        )
        
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, 'function_call') and part.function_call:
                return part.function_call
    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        return None
    
    return None

# --- Gemini Assistant Reply Function ---
async def generate_assistant_reply(message_text: str, existing_hooks: list[str]) -> str:
    """
    Генерирует ответ ассистента с учетом памяти пользователя.
    """
    system_prompt = (
        "Ты — ассистент. Вот что ты знаешь о пользователе: "
        f"{existing_hooks if existing_hooks else 'Пока ничего не известно.'} "
        "Используй эти факты для персонализации ответа. "
        "Если в памяти есть пожелания пользователя к стилю общения, обязательно учитывай их. "
        "Если пользователь выражает новые пожелания к стилю, запомни это как отдельный факт для будущих ответов. "
        "Не придумывай свою личность — твой стиль должен формироваться только на основе памяти о пользователе."
    )
    try:
        response = await model.generate_content_async(
            system_prompt + "\n\nСообщение пользователя: " + message_text,
            generation_config=GenerationConfig(temperature=0.7)
        )
        # 1. Пробуем response.text
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        # 2. Пробуем candidates[0].content.parts
        if hasattr(response, "candidates") and response.candidates:
            parts = getattr(response.candidates[0].content, "parts", None)
            if parts:
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        return part.text.strip()
        # 3. Fallback
        return "[Не удалось сгенерировать ответ.]"
    except Exception as e:
        print(f"❌ Error during Gemini assistant reply: {e}")
        return "[Внутренняя ошибка бота. Попробуйте позже или обратитесь к администратору.]" 