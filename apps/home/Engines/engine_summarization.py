from flask import Flask, request, jsonify
from langchain.chains import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

VERBOSE = True
MAX_TOKENS = 2048

STYLES = {
    "List": {
        "style": "Return your response as numbered list which covers the main points of the text and key facts and figures.",
        "trigger": "NUMBERED LIST SUMMARY WITH KEY POINTS AND FACTS",
    },
    "One sentence": {
        "style": "Return your response as one sentence which covers the main points of the text.",
        "trigger": "ONE SENTENCE SUMMARY",
    },
    "Consise": {
        "style": "Return your response as concise summary which covers the main points of the text.",
        "trigger": "CONCISE SUMMARY",
    },
    "Detailed": {
        "style": "Return your response as detailed summary which covers the main points of the text and key facts and figures.",
        "trigger": "DETAILED SUMMARY",
    },
}

# Chunk params in characters (not tokens)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

combine_prompt_template = """
Bolding any important phrases and/or statistics, generate a summary of the road defect report(s) that includes the following:

Overview: Highlight the main points, key facts, and figures.
Defect Detection: Emphasize the unique defects detected and their frequencies, with a focus on those with the highest frequency and severity. Do not give descriptions of the defects.
Defect Breakdown: Provide a breakdown of the different defect types, including defect type, frequency, date, and who reported them. Do not give descriptions of the defects.
Severity Listing: List the most severe defects detected, including relevant details.

The provided content to be summarized should have the following structure:
ReportID: __
InspectedBy: __,
InspectionDate: __,
GenerationTime: __,
Tags: [__, __, ...],
Defect(s): [__, __, ...],
DefectLikelihood(s): [__, __, ...], 
Severity: [__, __, ...].
{style}

```{content}```

{trigger} {in_language}:
"""

map_prompt_template = """
Bolding any important phrases and/or statistics, generate a concise summary of the road defect report(s) that includes the following:

Overview: Highlight the main points, key facts, and figures.
Defect Detection: Emphasize the unique defects detected and their frequencies, with a focus on those with the highest frequency and severity. Do not give descriptions of the defects.
Defect Breakdown: Provide a breakdown of the different defect types, including defect type, frequency, date, and who reported them. Do not give descriptions of the defects.
Severity Listing: List the most severe defects detected, including relevant details.

The provided content to be summarized should have the following structure:
ReportID: __
InspectedBy: __,
InspectionDate: __,
GenerationTime: __,
Tags: [__, __, ...],
Defect(s): [__, __, ...],
DefectLikelihood(s): [__, __, ...], 
Severity: [__, __, ...].
{text}

CONCISE SUMMARY {in_language}:
"""

# Initialize the LLM
llm = None
MODEL_CONTEXT_WINDOW = 8192

def load_llm(model_file, context_window, max_tokens, verbose):
    global llm
    if os.path.exists(model_file):
        llm = LlamaCpp(
            model_path=model_file,
            n_ctx=context_window,
            temperature=0,
            max_tokens=max_tokens,
            verbose=verbose,
        )
        return "Model loaded successfully"
    else:
        return "Model file does not exist"

@app.route('/api/load_model_llm', methods=['POST'])
def load_model_route():
    data = request.json
    home = os.getcwd()
    model_file = os.path.join(home, "models", "mistral-7b-openorca.Q3_K_S.gguf")
    message = load_llm(model_file, MODEL_CONTEXT_WINDOW, MAX_TOKENS, VERBOSE)
    logger.info('Model load requested.')
    return jsonify({'message': message})

@app.route('/summarize', methods=['POST'])
def summarize_route():
    if llm is None:
        return jsonify({'error': 'Model not loaded'}), 400

    data = request.json
    content = data.get('content')
    style = data.get('style', 'Consise')
    language = data.get('language', 'Default')
    logger.info(content)

    if not content:
        return jsonify({'error': 'content parameter is missing'}), 400

    summary, info = summarize_text(llm, content, style, language)
    logger.info('Summarization requested.')
    return jsonify({'summary': summary, 'info': info})

def summarize_base(llm, content, style, language):
    prompt = PromptTemplate.from_template(combine_prompt_template).partial(
        style=STYLES[style]["style"],
        trigger=STYLES[style]["trigger"],
        in_language=f"in {language}" if language != "Default" else "",
    )

    chain = LLMChain(llm=llm, prompt=prompt, verbose=VERBOSE)
    output = chain.run(content)

    return output

def summarize_map_reduce(llm, content, style, language):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    split_docs = text_splitter.create_documents([content])
    logger.info(
        f"Map-Reduce content splits ({len(split_docs)} splits): {[len(sd.page_content) for sd in split_docs]}")

    map_prompt = PromptTemplate.from_template(map_prompt_template).partial(
        in_language=f"in {language}" if language != "Default" else "",
    )
    combine_prompt = PromptTemplate.from_template(combine_prompt_template).partial(
        style=STYLES[style]["style"],
        trigger=STYLES[style]["trigger"],
        in_language=f"in {language}" if language != "Default" else "",
    )

    chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        combine_document_variable_name="content",
        verbose=VERBOSE,
    )

    output = chain.run(split_docs)
    return output

def summarize_text(llm, content, style, language="Default"):
    content_tokens = llm.get_num_tokens(content)

    info = f"Content length: {len(content)} chars, {content_tokens} tokens."

    base_threshold = MODEL_CONTEXT_WINDOW - MAX_TOKENS - 256

    start_time = time.perf_counter()

    if content_tokens < base_threshold:
        info += "\nUsing summarizer: base"
        logger.info("Using summarizer: base")
        summary = summarize_base(llm, content, style, language)
    else:
        info += "\nUsing summarizer: map-reduce"
        logger.info("Using summarizer: map-reduce")
        summary = summarize_map_reduce(llm, content, style, language)

    end_time = time.perf_counter()

    logger.info("Summary length: %d", len(summary))
    logger.info("Summary tokens: %d", llm.get_num_tokens(summary))
    logger.info("Summary:\n%s\n\n", summary)

    info += f"\nProcessing time: {round(end_time - start_time, 1)} secs."
    info += f"\nSummary length: {llm.get_num_tokens(summary)} tokens."

    logger.info("Info: %s", info)
    return summary, info

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=5007)