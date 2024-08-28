import os
import pandas as pd
import tiktoken
import asyncio
from dotenv import load_dotenv
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import GlobalCommunityContext
from graphrag.query.structured_search.global_search.search import GlobalSearch

load_dotenv(dotenv_path=".env")

api_key = os.getenv("GRAPHRAG_API_KEY")
llm_model = "gpt-4o-mini-2024-07-18"

llm = ChatOpenAI(api_key=api_key, model=llm_model, api_type=OpenaiApiType.OpenAI, max_retries=20)
token_encoder = tiktoken.get_encoding("cl100k_base")

script_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(script_dir, '..', 'input', 'artifacts')

entity_file = os.path.join(input_dir, 'create_final_nodes.parquet')
report_file = os.path.join(input_dir, 'create_final_community_reports.parquet')
entity_embedding_file = os.path.join(input_dir, 'create_final_entities.parquet')

entity_df = pd.read_parquet(entity_file)
report_df = pd.read_parquet(report_file)
entity_embedding_df = pd.read_parquet(entity_embedding_file)

reports = read_indexer_reports(report_df, entity_df, 2)
entities = read_indexer_entities(entity_df, entity_embedding_df, 2)

context_builder = GlobalCommunityContext(
    community_reports=reports,
    entities=entities,
    token_encoder=token_encoder,
)

context_builder_params = {
    "use_community_summary": False,
    "shuffle_data": True,
    "include_community_rank": True,
    "min_community_rank": 0,
    "community_rank_name": "rank",
    "include_community_weight": True,
    "community_weight_name": "occurrence weight",
    "normalize_community_weight": True,
    "max_tokens": 3_000,
    "context_name": "Reports",
}

map_llm_params = {
    "max_tokens": 1000,
    "temperature": 0.0,
    "response_format": {"type": "json_object"},
}

reduce_llm_params = {
    "max_tokens": 2000,
    "temperature": 0.0,
}

search_engine = GlobalSearch(
    llm=llm,
    context_builder=context_builder,
    token_encoder=token_encoder,
    max_data_tokens=12_000,
    map_llm_params=map_llm_params,
    reduce_llm_params=reduce_llm_params,
    allow_general_knowledge=False,
    json_mode=True,
    context_builder_params=context_builder_params,
    concurrent_coroutines=10,
    response_type="multiple-page report",
)

async def get_answer(query: str, short_term_memory: list) -> str:
    context = ' '.join(short_term_memory)
    search_query = f"Contesta en español, resumidamente en máximo unas 5 líneas y todo claro en un mismo texto, evita referencias y títulos, todo ello en lenguaje natural con el objetivo de ayudar y tranquilizar al paciente. Contexto: {context} /Contesta solo a la siguiente pregunta teniendo en cuenta el contexto, si no tiene nada que ver o no es necesario no es obligatorio utilizarlo. Pregunta: {query}"
    result = await search_engine.asearch(search_query)
    return result.response

def initialize_chatbot():
    pass




